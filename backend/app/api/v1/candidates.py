"""Candidates management endpoints"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.core.security import require_permission, PERM_VIEW_CANDIDATES, PERM_MANAGE_CVS, PERM_EDIT_OWN_CV
from app.db.session import get_db
from app.models import Availability, Candidate, Document, Section, Embedding

logger = get_logger(__name__)

router = APIRouter()


class CandidateListItem(BaseModel):
    """Candidate list item response"""

    id: str
    name: str
    email: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    years_experience: Optional[float]
    updated_at: str
    document_filename: Optional[str]
    embeddings_count: int
    availability_from: Optional[str]
    capacity_pct: Optional[int]


class CandidateListResponse(BaseModel):
    """Paginated candidate list response"""

    total: int
    page: int
    page_size: int
    candidates: List[CandidateListItem]


class SectionDetail(BaseModel):
    """Full section detail"""

    id: str
    type: str
    text: str


class AvailabilityDetail(BaseModel):
    """Availability detail"""

    id: str
    available_from: str
    capacity_pct: int
    notes: Optional[str]
    updated_at: str


class CandidateFullDetail(BaseModel):
    """Full candidate detail response"""

    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    years_experience: Optional[float]
    updated_at: str
    document_id: str
    document_filename: Optional[str]
    document_mime_type: Optional[str]
    embeddings_count: int
    availability: List[AvailabilityDetail]
    sections: List[SectionDetail]


class CandidateUpdate(BaseModel):
    """Candidate update request"""

    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)


@router.get("/", response_model=CandidateListResponse)
def list_candidates(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    _user: dict = Depends(require_permission(PERM_VIEW_CANDIDATES)),
    db: Session = Depends(get_db),
):
    """List all candidates with pagination and optional search"""

    # Build base query with eager loading of document
    query = db.query(Candidate).options(joinedload(Candidate.document))

    # Apply search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Candidate.name.ilike(search_filter)) | (Candidate.email.ilike(search_filter))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    candidates = query.order_by(Candidate.updated_at.desc()).offset(offset).limit(page_size).all()

    # Build response with availability info and embeddings count
    result_items = []
    for candidate in candidates:
        # Get earliest availability
        avail = (
            db.query(Availability)
            .filter(Availability.candidate_id == candidate.id)
            .order_by(Availability.available_from.asc())
            .first()
        )

        # Get embeddings count
        embeddings_count = (
            db.query(func.count(Embedding.id))
            .filter(Embedding.document_id == candidate.document_id)
            .scalar()
        ) or 0

        result_items.append(
            CandidateListItem(
                id=str(candidate.id),
                name=candidate.name,
                email=candidate.email,
                phone=candidate.phone,
                location=candidate.location,
                years_experience=candidate.years_experience,
                updated_at=candidate.updated_at.isoformat(),
                document_filename=candidate.document.filename if candidate.document else None,
                embeddings_count=embeddings_count,
                availability_from=avail.available_from.isoformat() if avail else None,
                capacity_pct=avail.capacity_pct if avail else None,
            )
        )

    return CandidateListResponse(
        total=total,
        page=page,
        page_size=page_size,
        candidates=result_items,
    )


@router.get("/{candidate_id}", response_model=CandidateFullDetail)
def get_candidate_full(
    candidate_id: str,
    _user: dict = Depends(require_permission(PERM_VIEW_CANDIDATES)),
    db: Session = Depends(get_db),
):
    """Get full candidate details including all sections"""

    try:
        candidate_uuid = UUID(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")

    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.document))
        .filter(Candidate.id == candidate_uuid)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get all sections
    sections = (
        db.query(Section)
        .filter(Section.document_id == candidate.document_id)
        .order_by(
            # Custom order: summary, skills, experience, certifications, full, others
            case(
                (Section.type == "summary", 1),
                (Section.type == "skills", 2),
                (Section.type == "experience", 3),
                (Section.type == "certifications", 4),
                (Section.type == "full", 5),
                else_=6,
            )
        )
        .all()
    )

    # Get all availability records
    avail_records = (
        db.query(Availability)
        .filter(Availability.candidate_id == candidate.id)
        .order_by(Availability.available_from.asc())
        .all()
    )

    # Get embeddings count
    embeddings_count = (
        db.query(func.count(Embedding.id))
        .filter(Embedding.document_id == candidate.document_id)
        .scalar()
    ) or 0

    return CandidateFullDetail(
        id=str(candidate.id),
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        years_experience=candidate.years_experience,
        updated_at=candidate.updated_at.isoformat(),
        document_id=str(candidate.document_id),
        document_filename=candidate.document.filename if candidate.document else None,
        document_mime_type=candidate.document.mime_type if candidate.document else None,
        embeddings_count=embeddings_count,
        availability=[
            AvailabilityDetail(
                id=str(a.id),
                available_from=a.available_from.isoformat(),
                capacity_pct=a.capacity_pct,
                notes=a.notes,
                updated_at=a.updated_at.isoformat(),
            )
            for a in avail_records
        ],
        sections=[
            SectionDetail(
                id=str(s.id),
                type=s.type,
                text=s.text,
            )
            for s in sections
        ],
    )


@router.put("/{candidate_id}")
def update_candidate(
    candidate_id: str,
    update_data: CandidateUpdate,
    user: dict = Depends(require_permission(PERM_MANAGE_CVS, PERM_EDIT_OWN_CV)),
    db: Session = Depends(get_db),
):
    """Update candidate core information"""

    try:
        candidate_uuid = UUID(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")

    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.document))
        .filter(Candidate.id == candidate_uuid)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Update fields
    update_dict = update_data.model_dump(exclude_none=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Phone edits are restricted to CV managers/superusers.
    if "phone" in update_dict:
        user_perms = set(user.get("permissions", []))
        if PERM_MANAGE_CVS not in user_perms:
            raise HTTPException(
                status_code=403,
                detail="Only super users/CV managers can edit phone information",
            )

    for field, value in update_dict.items():
        setattr(candidate, field, value)

    # Explicitly update the updated_at timestamp
    candidate.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(candidate)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update candidate")

    return {
        "id": str(candidate.id),
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "updated_at": candidate.updated_at.isoformat(),
    }
