"""Document ingestion endpoints"""
import base64
import hashlib
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import Agent, Candidate, Document, Embedding, Section
from app.services.cv_merge import get_cv_merge_service
from app.services.document_conversion import conversion_service
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
    # Manual fields if extraction fails
    manual_name: Optional[str] = None
    manual_email: Optional[str] = None
    manual_phone: Optional[str] = None


class IngestResponse(BaseModel):
    document_id: str
    candidate_id: Optional[str] = None
    sections_count: int
    embeddings_count: int
    # Required field validation
    missing_required_fields: Optional[List[str]] = None
    requires_manual_input: bool = False
    # Duplicate detection
    merge_proposal: Optional[Dict[str, Any]] = None
    requires_approval: bool = False


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

        if candidate:
            return IngestResponse(
                document_id=str(existing.id),
                candidate_id=str(candidate.id),
                sections_count=sections_count,
                embeddings_count=embeddings_count,
            )

        missing_fields = []
        if not req.manual_name or req.manual_name == "Unknown":
            missing_fields.append("name")
        if not req.manual_email:
            missing_fields.append("email")
        if not req.manual_phone:
            missing_fields.append("phone")

        if missing_fields:
            return IngestResponse(
                document_id=str(existing.id),
                candidate_id=None,
                sections_count=sections_count,
                embeddings_count=embeddings_count,
                missing_required_fields=missing_fields,
                requires_manual_input=True,
            )

        parsed = {
            "name": req.manual_name or "Unknown",
            "email": req.manual_email,
            "phone": req.manual_phone,
            "location": None,
        }

        merge_service = get_cv_merge_service(db)
        existing_candidate = merge_service.find_duplicate(
            name=parsed.get("name", "Unknown"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
        )

        if existing_candidate:
            sections = db.query(Section).filter(Section.document_id == existing.id).all()
            new_sections = [{"type": sec.type, "text": sec.text} for sec in sections]
            merge_proposal = merge_service.create_merge_proposal(
                existing_candidate, parsed, new_sections
            )

            return IngestResponse(
                document_id=str(existing.id),
                candidate_id=None,
                sections_count=sections_count,
                embeddings_count=embeddings_count,
                merge_proposal=merge_proposal,
                requires_approval=True,
            )

        candidate = Candidate(
            document_id=existing.id,
            name=parsed.get("name", "Unknown"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location"),
        )
        db.add(candidate)
        db.commit()

        return IngestResponse(
            document_id=str(existing.id),
            candidate_id=str(candidate.id),
            sections_count=sections_count,
            embeddings_count=embeddings_count,
            requires_manual_input=False,
            requires_approval=False,
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

    # Convert Word documents to PDF for better multi-column handling
    content_for_parsing = content
    mime_for_parsing = mime_type
    if mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        logger.info(f"Converting Word document to PDF: {req.filename}")
        pdf_content = conversion_service.word_to_pdf(content, mime_type)
        if pdf_content:
            content_for_parsing = pdf_content
            mime_for_parsing = "application/pdf"
            logger.info(f"Successfully converted to PDF ({len(pdf_content)} bytes)")
        else:
            logger.warning("Word to PDF conversion failed, using original content")

    # Parse document
    try:
        parser = parser_registry.get(req.document_type)
        parsed = parser.parse(content_for_parsing, mime_for_parsing, req.use_ocr)
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {e}")
    else:
        logger.info(
            "Parsed resume summary - name: %s, summary_len: %s, skills: %s, experience: %s, education: %s, certs: %s, raw_len: %s",
            parsed.get("name"),
            len(parsed.get("summary", "")),
            len(parsed.get("skills", [])),
            len(parsed.get("experience", [])),
            len(parsed.get("education", [])),
            len(parsed.get("certifications", [])),
            len(parsed.get("raw_text", "") or ""),
        )

    # Override with manual fields if provided
    if req.manual_name:
        parsed["name"] = req.manual_name
    if req.manual_email:
        parsed["email"] = req.manual_email
    if req.manual_phone:
        parsed["phone"] = req.manual_phone

    # Validate required fields
    missing_fields = []
    if not parsed.get("name") or parsed.get("name") == "Unknown":
        missing_fields.append("name")
    if not parsed.get("email"):
        missing_fields.append("email")
    if not parsed.get("phone"):
        missing_fields.append("phone")

    # If required fields are missing, return error asking for manual input
    if missing_fields and not (req.manual_name or req.manual_email or req.manual_phone):
        logger.warning(f"Missing required fields: {missing_fields}")
        # Create temporary document and sections for re-submission
        # but don't create candidate yet
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

        sections = _create_sections(db, doc.id, parsed)
        db.flush()

        # Create embeddings
        embeddings_service = get_embeddings_service()
        embeddings_count = _create_embeddings(
            db, doc.id, req.agent_id, sections, embeddings_service
        )
        db.commit()

        return IngestResponse(
            document_id=str(doc.id),
            candidate_id=None,
            sections_count=len(sections),
            embeddings_count=embeddings_count,
            missing_required_fields=missing_fields,
            requires_manual_input=True,
        )

    # Check for duplicates
    merge_service = get_cv_merge_service(db)
    existing_candidate = merge_service.find_duplicate(
        name=parsed.get("name", "Unknown"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
    )

    # Create document record (always - we want to keep both CVs)
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

    # If duplicate found, create merge proposal
    if existing_candidate:
        logger.info(f"Duplicate candidate found: {existing_candidate.id}")

        # Prepare sections for merge proposal
        new_sections = []
        for sec in sections:
            new_sections.append({
                "type": sec.type,
                "text": sec.text,
            })

        merge_proposal = merge_service.create_merge_proposal(
            existing_candidate, parsed, new_sections
        )

        db.commit()

        return IngestResponse(
            document_id=str(doc.id),
            candidate_id=None,  # Not linked yet, pending approval
            sections_count=len(sections),
            embeddings_count=embeddings_count,
            merge_proposal=merge_proposal,
            requires_approval=True,
        )

    # No duplicate - create new candidate record
    candidate = Candidate(
        document_id=doc.id,
        name=parsed.get("name", "Unknown"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
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
        requires_manual_input=False,
        requires_approval=False,
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

    logger.info(f"Creating sections from parsed data. Available keys: {list(parsed.keys())}")
    logger.info(f"Parsed data summary: raw_text={len(parsed.get('raw_text', '')) if parsed.get('raw_text') else 0} chars, "
               f"summary={len(parsed.get('summary', '')) if parsed.get('summary') else 0} chars, "
               f"skills={len(parsed.get('skills', []))} items, "
               f"experience={len(parsed.get('experience', []))} items, "
               f"certifications={len(parsed.get('certifications', []))} items")

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
        logger.info("Created summary section")

    # Skills section - store both raw and normalized
    if parsed.get("skills"):
        skills_text = ", ".join(parsed["skills"])
        sec = Section(
            document_id=document_id,
            type="skills",
            text=skills_text,
        )
        sections.append(sec)
        db.add(sec)
        logger.info(f"Created skills section with {len(parsed['skills'])} raw skills")

    # Skills normalized section - canonical ontology forms
    if parsed.get("skills_normalized"):
        skills_norm_text = ", ".join(parsed["skills_normalized"])
        sec = Section(
            document_id=document_id,
            type="skills_normalized",
            text=skills_norm_text,
        )
        sections.append(sec)
        db.add(sec)
        logger.info(f"Created normalized skills section with {len(parsed['skills_normalized'])} canonical skills")

    # Experience sections - include detected skills per role
    for idx, exp in enumerate(parsed.get("experience", [])):
        # Main experience text
        exp_text = f"{exp.get('org', '')} - {exp.get('role', '')}\n"
        exp_text += "\n".join(exp.get("bullets", []))

        # Add detected skills for this experience if available
        if exp.get("skills_normalized"):
            exp_text += f"\n\n[Skills detected: {', '.join(exp['skills_normalized'])}]"

        sec = Section(
            document_id=document_id,
            type="experience",
            text=exp_text,
        )
        sections.append(sec)
        db.add(sec)
    if parsed.get("experience"):
        logger.info(f"Created {len(parsed['experience'])} experience sections with per-role skill detection")

    # Certifications section - raw
    if parsed.get("certifications"):
        certs_text = "\n".join(parsed["certifications"])
        sec = Section(
            document_id=document_id,
            type="certifications",
            text=certs_text,
        )
        sections.append(sec)
        db.add(sec)
        logger.info(f"Created certifications section with {len(parsed['certifications'])} raw certs")

    # Certifications normalized section - canonical ontology forms
    if parsed.get("certifications_normalized"):
        certs_norm_text = "\n".join(parsed["certifications_normalized"])
        sec = Section(
            document_id=document_id,
            type="certifications_normalized",
            text=certs_norm_text,
        )
        sections.append(sec)
        db.add(sec)
        logger.info(f"Created normalized certifications section with {len(parsed['certifications_normalized'])} canonical certs")

    # Full document section - ALWAYS create this if we have any text
    raw_text = parsed.get("raw_text", "")
    if raw_text and raw_text.strip():
        sec = Section(
            document_id=document_id,
            type="full",
            text=raw_text.strip()[:10000],  # Limit size
        )
        sections.append(sec)
        db.add(sec)
        logger.info(f"Created full document section ({len(raw_text)} chars, truncated to {len(raw_text.strip()[:10000])})")
    else:
        logger.warning("⚠️ No raw_text found in parsed data - cannot create full document section!")

    if not sections:
        logger.error("❌ NO SECTIONS CREATED! This means parsing returned completely empty data.")
    else:
        logger.info(f"✅ Created {len(sections)} sections total")

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
        logger.warning("No sections with text found for embedding creation")
        return 0

    try:
        logger.info(f"Creating embeddings for {len(texts)} sections using {embeddings_service.provider} provider")
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

        logger.info(f"Successfully created {len(vectors)} embeddings (dimension={dim})")
        return len(vectors)
    except Exception as e:
        logger.error(f"❌ EMBEDDING CREATION FAILED: {e}")
        logger.error(f"Provider: {embeddings_service.provider}, Model: {embeddings_service.model}")
        logger.error("Possible causes:")
        logger.error("  1. sentence-transformers not installed: pip install sentence-transformers")
        logger.error("  2. Model not downloaded (will download on first use, requires internet)")
        logger.error("  3. OpenAI API key not set (if using EMBEDDINGS_PROVIDER=openai)")
        import traceback
        logger.error(f"Full error: {traceback.format_exc()}")
        return 0


class MergeApprovalRequest(BaseModel):
    candidate_id: str
    new_document_id: str
    approved_data: Dict[str, Any]


class MergeApprovalResponse(BaseModel):
    success: bool
    candidate_id: str
    message: str


@router.post("/approve-merge", response_model=MergeApprovalResponse)
def approve_merge(req: MergeApprovalRequest, db: Session = Depends(get_db)):
    """Approve and apply CV merge for duplicate candidate"""

    try:
        merge_service = get_cv_merge_service(db)

        # Apply the merge
        candidate = merge_service.apply_merge(
            candidate_id=uuid.UUID(req.candidate_id),
            approved_data=req.approved_data,
            new_document_id=uuid.UUID(req.new_document_id),
        )

        # Link the new document to the candidate
        # (the new document already exists with sections and embeddings)
        new_doc = db.query(Document).filter(Document.id == uuid.UUID(req.new_document_id)).first()

        if new_doc:
            # Update the candidate's primary document to the most recent one
            candidate.document_id = new_doc.id
            db.commit()

        logger.info(f"Merge approved and applied for candidate {candidate.id}")

        return MergeApprovalResponse(
            success=True,
            candidate_id=str(candidate.id),
            message="Merge successfully applied. Both CVs are now linked to this candidate.",
        )

    except Exception as e:
        logger.error(f"Merge approval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Merge approval failed: {e}")
