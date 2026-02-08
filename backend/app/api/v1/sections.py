"""Section management endpoints"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import require_permission, PERM_MANAGE_CVS, PERM_EDIT_OWN_CV
from app.db.session import get_db
from app.models import Section, Document, Candidate, Embedding
from app.services.embeddings import get_embeddings_service

logger = get_logger(__name__)

router = APIRouter()


class SectionUpdateRequest(BaseModel):
    """Request to update a section's text"""

    text: str = Field(..., min_length=1, max_length=50000, description="Updated section text")


class SectionUpdateResponse(BaseModel):
    """Response after updating a section"""

    id: str
    type: str
    text: str
    updated: bool
    embeddings_regenerated: bool


@router.put("/{section_id}", response_model=SectionUpdateResponse)
def update_section(
    section_id: str,
    update_data: SectionUpdateRequest,
    _user: dict = Depends(require_permission(PERM_MANAGE_CVS, PERM_EDIT_OWN_CV)),
    db: Session = Depends(get_db),
):
    """Update a section's text content and regenerate embeddings

    Allows editing of CV sections like skills, certifications, experience, etc.
    Automatically regenerates embeddings for the updated section to maintain
    semantic search accuracy.
    """
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    # Get the section
    section = db.query(Section).filter(Section.id == section_uuid).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Check if this section type can be edited
    # Allow editing of most section types except internal ones
    non_editable_types = ["full", "raw_text"]
    if section.type in non_editable_types:
        raise HTTPException(
            status_code=400,
            detail=f"Section type '{section.type}' cannot be edited directly"
        )

    # Update the section text
    old_text = section.text
    section.text = update_data.text

    try:
        db.commit()
        db.refresh(section)

        # Get document for agent_id (needed for embeddings)
        document = db.query(Document).filter(Document.id == section.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Also update the candidate's updated_at timestamp
        candidate = (
            db.query(Candidate)
            .join(Document)
            .filter(Document.id == section.document_id)
            .first()
        )
        if candidate:
            from datetime import datetime
            candidate.updated_at = datetime.utcnow()
            db.commit()

        logger.info(
            f"Section {section_id} updated: type={section.type}, "
            f"old_length={len(old_text)}, new_length={len(update_data.text)}"
        )

        # Regenerate embeddings for the updated section
        embeddings_regenerated = False
        try:
            # Delete old embeddings for this section
            old_embeddings = db.query(Embedding).filter(Embedding.section_id == section.id).all()
            for emb in old_embeddings:
                db.delete(emb)
            db.flush()

            logger.info(f"Deleted {len(old_embeddings)} old embeddings for section {section_id}")

            # Generate new embeddings
            embeddings_service = get_embeddings_service()
            vectors = embeddings_service.embed_texts([section.text], document.agent_id)
            dim = embeddings_service.get_dimension()

            # Store new embedding
            if vectors and len(vectors) > 0:
                new_embedding = Embedding(
                    document_id=document.id,
                    section_id=section.id,
                    agent_id=document.agent_id,
                    model=embeddings_service.model,
                    dim=dim,
                    vector=vectors[0].tolist(),
                )
                db.add(new_embedding)
                db.commit()
                embeddings_regenerated = True
                logger.info(f"Successfully regenerated embedding for section {section_id} (dim={dim})")
            else:
                logger.warning(f"No vectors generated for section {section_id}")

        except Exception as e:
            # Log error but don't fail the update - text was already saved
            logger.error(f"Failed to regenerate embeddings for section {section_id}: {e}")
            logger.warning("Section text was updated but embeddings were not regenerated")
            # Don't rollback - we want to keep the text update

        return SectionUpdateResponse(
            id=str(section.id),
            type=section.type,
            text=section.text,
            updated=True,
            embeddings_regenerated=embeddings_regenerated,
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update section {section_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update section")


@router.delete("/{section_id}")
def delete_section(
    section_id: str,
    _user: dict = Depends(require_permission(PERM_MANAGE_CVS)),
    db: Session = Depends(get_db),
):
    """Delete a section

    Use with caution - this will also delete associated embeddings.
    """
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    section = db.query(Section).filter(Section.id == section_uuid).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Don't allow deleting critical sections
    critical_types = ["summary", "full"]
    if section.type in critical_types:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete critical section type '{section.type}'"
        )

    try:
        db.delete(section)
        db.commit()

        logger.info(f"Section {section_id} deleted: type={section.type}")

        return {"id": section_id, "deleted": True}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete section {section_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete section")
