"""Async document upload endpoints with progress tracking"""
import base64
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import require_permission, PERM_UPLOAD_CV, PERM_MANAGE_CVS
from app.db.session import get_db
from app.models import Agent, Candidate, Document, Embedding, Section, UploadJob, UploadStatus
from app.services.cv_merge import get_cv_merge_service
from app.services.document_conversion import conversion_service
from app.services.embeddings import get_embeddings_service
from app.services.experience import calculate_total_years_experience
from app.services.normalize import get_normalize_service
from app.services.parsing.parser_registry import parser_registry
from app.services.parsing.resume_parser import ResumeParser

logger = get_logger(__name__)

router = APIRouter()

# Register parsers
parser_registry.register("resume", ResumeParser())


class UploadRequest(BaseModel):
    agent_id: str
    document_type: str
    filename: str
    content_base64: str
    use_ocr: bool = False


class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    document_id: Optional[str] = None
    candidate_id: Optional[str] = None
    missing_fields: Optional[List[str]] = None
    error_message: Optional[str] = None
    sections_count: int = 0
    embeddings_count: int = 0
    merge_proposal: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class CompleteUploadRequest(BaseModel):
    job_id: str
    manual_name: Optional[str] = None
    manual_email: Optional[str] = None
    manual_phone: Optional[str] = None


@router.post("/upload-async", response_model=UploadResponse)
async def upload_cv_async(
    req: UploadRequest,
    background_tasks: BackgroundTasks,
    _user: dict = Depends(require_permission(PERM_UPLOAD_CV, PERM_MANAGE_CVS)),
    db: Session = Depends(get_db),
):
    """
    Upload CV for async processing with progress tracking.
    Returns immediately with a job ID that can be used to poll for status.
    """
    try:
        # Create upload job
        job = UploadJob(
            filename=req.filename,
            agent_id=req.agent_id,
            status=UploadStatus.QUEUED,
            progress=0,
            current_step="Queued for processing"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created upload job {job.id} for file {req.filename}")

        # Start background processing
        background_tasks.add_task(
            process_cv_async,
            job_id=str(job.id),
            content_base64=req.content_base64,
            agent_id=req.agent_id,
            document_type=req.document_type,
            filename=req.filename,
            use_ocr=req.use_ocr
        )

        return UploadResponse(
            job_id=str(job.id),
            status=UploadStatus.QUEUED,
            message=f"Upload queued successfully. Use job_id to check status."
        )

    except Exception as e:
        logger.error(f"Failed to queue upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue upload: {e}")


@router.get("/upload-status/{job_id}", response_model=JobStatusResponse)
def get_upload_status(
    job_id: str,
    _user: dict = Depends(require_permission(PERM_UPLOAD_CV, PERM_MANAGE_CVS)),
    db: Session = Depends(get_db),
):
    """Get the status of an upload job"""
    try:
        job = db.query(UploadJob).filter(UploadJob.id == uuid.UUID(job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            document_id=str(job.document_id) if job.document_id else None,
            candidate_id=str(job.candidate_id) if job.candidate_id else None,
            missing_fields=job.missing_fields,
            error_message=job.error_message,
            sections_count=job.sections_count,
            embeddings_count=job.embeddings_count,
            merge_proposal=job.merge_proposal,
            requires_approval=job.requires_approval,
            created_at=job.created_at.isoformat() if job.created_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {e}")


@router.post("/complete-upload")
def complete_upload_with_manual_data(
    req: CompleteUploadRequest,
    _user: dict = Depends(require_permission(PERM_UPLOAD_CV, PERM_MANAGE_CVS)),
    db: Session = Depends(get_db),
):
    """
    Complete an upload that requires manual data entry.
    Called after user provides missing name/email/phone.
    """
    try:
        job = db.query(UploadJob).filter(UploadJob.id == uuid.UUID(req.job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != UploadStatus.REQUIRES_INPUT:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not awaiting input (status: {job.status})"
            )

        if not job.document_id:
            raise HTTPException(status_code=400, detail="No document associated with job")

        # Retrieve the document and sections
        document = db.query(Document).filter(Document.id == job.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Build parsed data from manual inputs
        parsed = {
            "name": req.manual_name or "Unknown",
            "email": req.manual_email,
            "phone": req.manual_phone,
            "location": None,
        }

        # Validate required fields
        missing = []
        if not parsed.get("name") or parsed["name"] == "Unknown":
            missing.append("name")
        if not parsed.get("email"):
            missing.append("email")
        if not parsed.get("phone"):
            missing.append("phone")

        if missing:
            job.missing_fields = missing
            db.commit()
            return {
                "success": False,
                "missing_fields": missing,
                "message": "Still missing required fields"
            }

        # Check for duplicates
        merge_service = get_cv_merge_service(db)
        existing_candidate = merge_service.find_duplicate(
            name=parsed.get("name", "Unknown"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
        )

        if existing_candidate:
            sections = db.query(Section).filter(Section.document_id == job.document_id).all()
            new_sections = [{"type": sec.type, "text": sec.text} for sec in sections]
            merge_proposal = merge_service.create_merge_proposal(
                existing_candidate, parsed, new_sections
            )

            job.status = UploadStatus.COMPLETED
            job.progress = 100
            job.current_step = "Awaiting merge approval"
            job.merge_proposal = merge_proposal
            job.requires_approval = True
            job.completed_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "requires_approval": True,
                "merge_proposal": merge_proposal,
                "document_id": str(job.document_id),
                "message": "Duplicate found - awaiting merge approval"
            }

        # No duplicate - create candidate
        candidate = Candidate(
            document_id=job.document_id,
            name=parsed.get("name", "Unknown"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location"),
            years_experience=calculate_total_years_experience(parsed.get("experience", [])),
        )
        db.add(candidate)
        db.flush()

        job.status = UploadStatus.COMPLETED
        job.progress = 100
        job.current_step = "Completed"
        job.candidate_id = candidate.id
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Completed upload job {job.id} with manual data")

        return {
            "success": True,
            "candidate_id": str(candidate.id),
            "document_id": str(job.document_id),
            "message": "CV processed successfully"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Failed to complete upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete upload: {e}")


def process_cv_async(
    job_id: str,
    content_base64: str,
    agent_id: str,
    document_type: str,
    filename: str,
    use_ocr: bool = False
):
    """
    Background task to process CV asynchronously.
    Updates job status and progress as it goes.
    """
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(UploadJob).filter(UploadJob.id == uuid.UUID(job_id)).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update status to processing
        job.status = UploadStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.progress = 5
        job.current_step = "Decoding file content"
        db.commit()

        # Decode content
        try:
            content = base64.b64decode(content_base64)
        except Exception as e:
            job.status = UploadStatus.FAILED
            job.error_message = f"Invalid base64 content: {e}"
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        # Compute hash
        job.progress = 10
        job.current_step = "Computing file hash"
        db.commit()

        sha256 = hashlib.sha256(content).hexdigest()

        # Check if document already exists
        job.progress = 15
        job.current_step = "Checking for duplicates"
        db.commit()

        existing = db.query(Document).filter(Document.sha256 == sha256).first()
        if existing:
            logger.info(f"Document already exists: {sha256}")
            candidate = db.query(Candidate).filter(Candidate.document_id == existing.id).first()

            job.document_id = existing.id
            job.candidate_id = candidate.id if candidate else None
            job.sections_count = db.query(Section).filter(Section.document_id == existing.id).count()
            job.embeddings_count = db.query(Embedding).filter(Embedding.document_id == existing.id).count()

            if not candidate:
                job.status = UploadStatus.REQUIRES_INPUT
                job.missing_fields = ["name", "email", "phone"]
                job.progress = 100
                job.current_step = "Awaiting required information"
            else:
                job.status = UploadStatus.COMPLETED
                job.progress = 100
                job.current_step = "Already processed"

            job.completed_at = datetime.utcnow()
            db.commit()
            return

        # Ensure agent exists
        job.progress = 20
        job.current_step = "Validating agent"
        db.commit()

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            agent = Agent(id=agent_id, name=agent_id.title())
            db.add(agent)
            db.commit()

        # Store original
        job.progress = 25
        job.current_step = "Storing file"
        db.commit()

        from app.services.storage import storage_service
        mime_type = _guess_mime_type(filename)
        storage_key = storage_service.store(sha256, content, mime_type)

        # Convert Word documents to PDF
        job.progress = 30
        job.current_step = "Converting document format"
        db.commit()

        content_for_parsing = content
        mime_for_parsing = mime_type
        if mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            logger.info(f"Converting Word document to PDF: {filename}")
            pdf_content = conversion_service.word_to_pdf(content, mime_type)
            if pdf_content:
                content_for_parsing = pdf_content
                mime_for_parsing = "application/pdf"

        # Parse document
        job.progress = 40
        job.current_step = "Extracting text from document"
        db.commit()

        try:
            parser = parser_registry.get(document_type)
            parsed = parser.parse(content_for_parsing, mime_for_parsing, use_ocr)
        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            job.status = UploadStatus.FAILED
            job.error_message = f"Parsing failed: {e}"
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        # Create document record
        job.progress = 60
        job.current_step = "Creating document record"
        db.commit()

        doc = Document(
            sha256=sha256,
            agent_id=agent_id,
            document_type=document_type,
            filename=filename,
            mime_type=mime_type,
            ocr=use_ocr,
            version=1,
        )
        db.add(doc)
        db.flush()

        job.document_id = doc.id
        db.commit()

        # Create sections
        job.progress = 70
        job.current_step = "Processing document sections"
        db.commit()

        sections = _create_sections(db, doc.id, parsed)
        db.flush()

        job.sections_count = len(sections)
        db.commit()

        # Normalize skills and certs
        job.progress = 80
        job.current_step = "Normalizing skills and certifications"
        db.commit()

        normalize_service = get_normalize_service(agent_id)
        normalized_skills = normalize_service.normalize_skills(parsed.get("skills", []))

        # Create embeddings
        job.progress = 85
        job.current_step = "Creating embeddings"
        db.commit()

        embeddings_service = get_embeddings_service()
        embeddings_count = _create_embeddings(
            db, doc.id, agent_id, sections, embeddings_service
        )

        job.embeddings_count = embeddings_count
        db.commit()

        # Validate required fields
        job.progress = 90
        job.current_step = "Validating extracted data"
        db.commit()

        missing_fields = []
        if not parsed.get("name") or parsed.get("name") == "Unknown":
            missing_fields.append("name")
        if not parsed.get("email"):
            missing_fields.append("email")
        if not parsed.get("phone"):
            missing_fields.append("phone")

        if missing_fields:
            job.status = UploadStatus.REQUIRES_INPUT
            job.missing_fields = missing_fields
            job.progress = 100
            job.current_step = "Awaiting required information"
            job.completed_at = datetime.utcnow()
            db.commit()
            logger.warning(f"Job {job_id} requires manual input: {missing_fields}")
            return

        # Check for duplicates
        job.progress = 95
        job.current_step = "Checking for duplicate candidates"
        db.commit()

        merge_service = get_cv_merge_service(db)
        existing_candidate = merge_service.find_duplicate(
            name=parsed.get("name", "Unknown"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
        )

        if existing_candidate:
            new_sections = [{"type": sec.type, "text": sec.text} for sec in sections]
            merge_proposal = merge_service.create_merge_proposal(
                existing_candidate, parsed, new_sections
            )

            job.status = UploadStatus.COMPLETED
            job.progress = 100
            job.current_step = "Awaiting merge approval"
            job.merge_proposal = merge_proposal
            job.requires_approval = True
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        # Create candidate
        job.progress = 98
        job.current_step = "Creating candidate profile"
        db.commit()

        candidate = Candidate(
            document_id=doc.id,
            name=parsed.get("name", "Unknown"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location"),
            years_experience=calculate_total_years_experience(parsed.get("experience", [])),
        )
        db.add(candidate)
        db.flush()

        job.status = UploadStatus.COMPLETED
        job.progress = 100
        job.current_step = "Completed successfully"
        job.candidate_id = candidate.id
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Completed job {job_id}: document {doc.id}, candidate {candidate.id}")

    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

        try:
            job = db.query(UploadJob).filter(UploadJob.id == uuid.UUID(job_id)).first()
            if job:
                job.status = UploadStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass

    finally:
        db.close()


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

    # Skills normalized section
    if parsed.get("skills_normalized"):
        skills_norm_text = ", ".join(parsed["skills_normalized"])
        sec = Section(
            document_id=document_id,
            type="skills_normalized",
            text=skills_norm_text,
        )
        sections.append(sec)
        db.add(sec)

    # Experience sections
    for idx, exp in enumerate(parsed.get("experience", [])):
        exp_text = f"{exp.get('org', '')} - {exp.get('role', '')}\n"
        exp_text += "\n".join(exp.get("bullets", []))
        if exp.get("skills_normalized"):
            exp_text += f"\n\n[Skills detected: {', '.join(exp['skills_normalized'])}]"

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

    # Certifications normalized section
    if parsed.get("certifications_normalized"):
        certs_norm_text = "\n".join(parsed["certifications_normalized"])
        sec = Section(
            document_id=document_id,
            type="certifications_normalized",
            text=certs_norm_text,
        )
        sections.append(sec)
        db.add(sec)

    # Full document section
    raw_text = parsed.get("raw_text", "")
    if raw_text and raw_text.strip():
        sec = Section(
            document_id=document_id,
            type="full",
            text=raw_text.strip()[:10000],
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
