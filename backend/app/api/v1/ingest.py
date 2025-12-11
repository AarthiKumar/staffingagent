"""Document ingestion endpoints"""
import base64
import hashlib
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import Agent, Candidate, Document, Embedding, Section
from app.services.embeddings import get_embeddings_service
from app.services.normalize import get_normalize_service
from app.services.parsing.parser_registry import parser_registry
from app.services.parsing.resume_parser import ResumeParser
from app.services.storage import storage_service

logger = get_logger(__name__)

router = APIRouter()

# Register parsers
parser_registry.register("resume", ResumeParser())


class IngestRequest(BaseModel):
    agent_id: str
    document_type: str
    filename: str
    content_base64: str
    use_ocr: bool = False


class IngestResponse(BaseModel):
    document_id: str
    candidate_id: Optional[str]
    sections_count: int
    embeddings_count: int


@router.post("/", response_model=IngestResponse)
def ingest_document(req: IngestRequest, db: Session = Depends(get_db)):
    """Ingest a document (resume, etc.)"""

    # Decode content
    try:
        content = base64.b64decode(req.content_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e}")

    # Compute hash
    sha256 = hashlib.sha256(content).hexdigest()

    # Check if document already exists
    existing = db.query(Document).filter(Document.sha256 == sha256).first()
    if existing:
        logger.info(f"Document already exists: {sha256}")
        candidate = db.query(Candidate).filter(Candidate.document_id == existing.id).first()
        sections_count = db.query(Section).filter(Section.document_id == existing.id).count()
        embeddings_count = db.query(Embedding).filter(Embedding.document_id == existing.id).count()

        return IngestResponse(
            document_id=str(existing.id),
            candidate_id=str(candidate.id) if candidate else None,
            sections_count=sections_count,
            embeddings_count=embeddings_count,
        )

    # Ensure agent exists
    agent = db.query(Agent).filter(Agent.id == req.agent_id).first()
    if not agent:
        agent = Agent(id=req.agent_id, name=req.agent_id.title())
        db.add(agent)
        db.commit()

    # Store original
    mime_type = _guess_mime_type(req.filename)
    storage_key = storage_service.store(sha256, content, mime_type)

    # Parse document
    try:
        parser = parser_registry.get(req.document_type)
        parsed = parser.parse(content, mime_type, req.use_ocr)
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {e}")

    # Create document record
    doc = Document(
        sha256=sha256,
        agent_id=req.agent_id,
        document_type=req.document_type,
        filename=req.filename,
        mime_type=mime_type,
        ocr=req.use_ocr,
        version=1,
    )
    db.add(doc)
    db.flush()

    # Create sections
    sections = _create_sections(db, doc.id, parsed)
    db.flush()

    # Normalize skills and certs
    normalize_service = get_normalize_service(req.agent_id)
    normalized_skills = normalize_service.normalize_skills(parsed.get("skills", []))

    # Create embeddings
    embeddings_service = get_embeddings_service()
    embeddings_count = _create_embeddings(
        db, doc.id, req.agent_id, sections, embeddings_service
    )

    # Create candidate record
    candidate = Candidate(
        document_id=doc.id,
        name=parsed.get("name", "Unknown"),
        email=parsed.get("email"),
        location=parsed.get("location"),
    )
    db.add(candidate)
    db.commit()

    logger.info(
        f"Ingested document {doc.id}: {len(sections)} sections, {embeddings_count} embeddings"
    )

    return IngestResponse(
        document_id=str(doc.id),
        candidate_id=str(candidate.id),
        sections_count=len(sections),
        embeddings_count=embeddings_count,
    )


def _guess_mime_type(filename: str) -> str:
    """Guess MIME type from filename"""
    ext = filename.lower().split(".")[-1]
    mime_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "txt": "text/plain",
    }
    return mime_map.get(ext, "application/octet-stream")


def _create_sections(db: Session, document_id: uuid.UUID, parsed: dict) -> list[Section]:
    """Create section records from parsed data"""
    sections = []

    # Summary section
    if parsed.get("summary"):
        sec = Section(
            document_id=document_id,
            type="summary",
            text=parsed["summary"],
            start_idx=0,
            end_idx=len(parsed["summary"]),
        )
        sections.append(sec)
        db.add(sec)

    # Skills section
    if parsed.get("skills"):
        skills_text = ", ".join(parsed["skills"])
        sec = Section(
            document_id=document_id,
            type="skills",
            text=skills_text,
        )
        sections.append(sec)
        db.add(sec)

    # Experience sections
    for idx, exp in enumerate(parsed.get("experience", [])):
        exp_text = f"{exp.get('org', '')} - {exp.get('role', '')}\n"
        exp_text += "\n".join(exp.get("bullets", []))
        sec = Section(
            document_id=document_id,
            type="experience",
            text=exp_text,
        )
        sections.append(sec)
        db.add(sec)

    # Certifications section
    if parsed.get("certifications"):
        certs_text = "\n".join(parsed["certifications"])
        sec = Section(
            document_id=document_id,
            type="certifications",
            text=certs_text,
        )
        sections.append(sec)
        db.add(sec)

    # Full document section
    if parsed.get("raw_text"):
        sec = Section(
            document_id=document_id,
            type="full",
            text=parsed["raw_text"][:10000],  # Limit size
        )
        sections.append(sec)
        db.add(sec)

    return sections


def _create_embeddings(
    db: Session,
    document_id: uuid.UUID,
    agent_id: str,
    sections: list[Section],
    embeddings_service,
) -> int:
    """Create embedding records for sections"""
    texts = [s.text for s in sections if s.text]
    if not texts:
        return 0

    try:
        vectors = embeddings_service.embed_texts(texts, agent_id)
        dim = embeddings_service.get_dimension()

        for section, vector in zip(sections, vectors):
            emb = Embedding(
                document_id=document_id,
                section_id=section.id,
                agent_id=agent_id,
                model=embeddings_service.model,
                dim=dim,
                vector=vector.tolist(),
            )
            db.add(emb)

        return len(vectors)
    except Exception as e:
        logger.error(f"Embedding creation failed: {e}")
        return 0
