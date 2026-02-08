"""Availability management endpoints"""
import csv
import io
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import (
    get_current_user,
    require_permission,
    PERM_MANAGE_AVAILABILITY,
    PERM_EDIT_OWN_AVAILABILITY,
    PERM_SEARCH_CANDIDATES,
)
from app.db.session import get_db
from app.models import Availability, Candidate, User

logger = get_logger(__name__)

router = APIRouter()


class AvailabilityUpdate(BaseModel):
    candidate_id: str
    available_from: str  # ISO date
    available_to: Optional[str] = None  # ISO date, nullable
    capacity_pct: int
    notes: Optional[str] = None


class AvailabilityResponse(BaseModel):
    id: str
    candidate_id: str
    candidate_name: str
    available_from: str
    available_to: Optional[str]
    capacity_pct: int
    notes: Optional[str]


@router.get("/", response_model=List[AvailabilityResponse])
def list_availability(
    _user: dict = Depends(require_permission(PERM_MANAGE_AVAILABILITY, PERM_SEARCH_CANDIDATES)),
    db: Session = Depends(get_db),
):
    """List all availability records"""

    records = (
        db.query(Availability)
        .join(Candidate)
        .order_by(Availability.available_from.asc())
        .all()
    )

    return [_to_response(a) for a in records]


@router.put("/{candidate_id}", response_model=AvailabilityResponse)
def update_availability(
    candidate_id: str,
    req: AvailabilityUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update availability for a candidate"""

    # Check permissions: manage:availability for anyone, or edit:own_availability for own
    user_perms = set(current_user.get("permissions", []))
    if PERM_MANAGE_AVAILABILITY not in user_perms:
        if PERM_EDIT_OWN_AVAILABILITY in user_perms:
            # Candidate can only edit their own availability
            user_record = db.query(User).filter(User.auth0_sub == current_user["sub"]).first()
            if not user_record or str(user_record.candidate_id) != candidate_id:
                raise HTTPException(status_code=403, detail="Can only update your own availability")
        else:
            raise HTTPException(status_code=403, detail="Missing required permission")

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Parse dates
    try:
        avail_from = date.fromisoformat(req.available_from)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid available_from date format")

    avail_to = None
    if req.available_to:
        try:
            avail_to = date.fromisoformat(req.available_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid available_to date format")

    # Upsert: match on candidate + start date
    existing = (
        db.query(Availability)
        .filter(
            Availability.candidate_id == candidate_id,
            Availability.available_from == avail_from,
        )
        .first()
    )

    if existing:
        existing.available_to = avail_to
        existing.capacity_pct = req.capacity_pct
        existing.notes = req.notes
        avail = existing
    else:
        avail = Availability(
            candidate_id=candidate_id,
            available_from=avail_from,
            available_to=avail_to,
            capacity_pct=req.capacity_pct,
            notes=req.notes,
        )
        db.add(avail)

    db.commit()
    db.refresh(avail)

    return _to_response(avail)


@router.post("/upload")
def upload_availability_csv(
    file: UploadFile = File(...),
    _user: dict = Depends(require_permission(PERM_MANAGE_AVAILABILITY)),
    db: Session = Depends(get_db),
):
    """Upload availability data from CSV (requires manage:availability permission)"""

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")

    try:
        content = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        created = 0
        updated = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                candidate_email = row.get("email", "").strip()
                avail_from_str = row.get("available_from", "").strip()
                avail_to_str = row.get("available_to", "").strip()
                capacity_pct_str = row.get("capacity_pct", "").strip()
                notes = row.get("notes", "").strip()

                if not candidate_email or not avail_from_str or not capacity_pct_str:
                    errors.append(f"Row {row_num}: Missing required fields")
                    continue

                candidate = db.query(Candidate).filter(Candidate.email == candidate_email).first()
                if not candidate:
                    errors.append(f"Row {row_num}: Candidate not found: {candidate_email}")
                    continue

                avail_from = date.fromisoformat(avail_from_str)
                avail_to = date.fromisoformat(avail_to_str) if avail_to_str else None
                capacity_pct = int(capacity_pct_str)

                existing = (
                    db.query(Availability)
                    .filter(
                        Availability.candidate_id == candidate.id,
                        Availability.available_from == avail_from,
                    )
                    .first()
                )

                if existing:
                    existing.available_to = avail_to
                    existing.capacity_pct = capacity_pct
                    existing.notes = notes or existing.notes
                    updated += 1
                else:
                    avail = Availability(
                        candidate_id=candidate.id,
                        available_from=avail_from,
                        available_to=avail_to,
                        capacity_pct=capacity_pct,
                        notes=notes,
                    )
                    db.add(avail)
                    created += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        db.commit()

        return {"created": created, "updated": updated, "errors": errors}

    except Exception as e:
        logger.error(f"CSV upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


def _to_response(a: Availability) -> AvailabilityResponse:
    return AvailabilityResponse(
        id=str(a.id),
        candidate_id=str(a.candidate_id),
        candidate_name=a.candidate.name,
        available_from=a.available_from.isoformat(),
        available_to=a.available_to.isoformat() if a.available_to else None,
        capacity_pct=a.capacity_pct,
        notes=a.notes,
    )
