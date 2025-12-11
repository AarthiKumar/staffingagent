"""Availability management endpoints"""
import csv
import io
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import Availability, Candidate

logger = get_logger(__name__)

router = APIRouter()


class AvailabilityUpdate(BaseModel):
    candidate_id: str
    available_from: str  # ISO date
    capacity_pct: int
    notes: Optional[str] = None


class AvailabilityResponse(BaseModel):
    id: str
    candidate_id: str
    candidate_name: str
    available_from: str
    capacity_pct: int
    notes: Optional[str]


@router.get("/", response_model=List[AvailabilityResponse])
def list_availability(db: Session = Depends(get_db)):
    """List all availability records"""

    records = (
        db.query(Availability)
        .join(Candidate)
        .order_by(Availability.available_from.asc())
        .all()
    )

    return [
        AvailabilityResponse(
            id=str(a.id),
            candidate_id=str(a.candidate_id),
            candidate_name=a.candidate.name,
            available_from=a.available_from.isoformat(),
            capacity_pct=a.capacity_pct,
            notes=a.notes,
        )
        for a in records
    ]


@router.put("/{candidate_id}", response_model=AvailabilityResponse)
def update_availability(
    candidate_id: str,
    req: AvailabilityUpdate,
    db: Session = Depends(get_db),
):
    """Update availability for a candidate"""

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Parse date
    try:
        avail_date = date.fromisoformat(req.available_from)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Check if record exists
    existing = (
        db.query(Availability)
        .filter(
            Availability.candidate_id == candidate_id,
            Availability.available_from == avail_date,
        )
        .first()
    )

    if existing:
        # Update existing
        existing.capacity_pct = req.capacity_pct
        existing.notes = req.notes
        avail = existing
    else:
        # Create new
        avail = Availability(
            candidate_id=candidate_id,
            available_from=avail_date,
            capacity_pct=req.capacity_pct,
            notes=req.notes,
        )
        db.add(avail)

    db.commit()
    db.refresh(avail)

    return AvailabilityResponse(
        id=str(avail.id),
        candidate_id=str(avail.candidate_id),
        candidate_name=candidate.name,
        available_from=avail.available_from.isoformat(),
        capacity_pct=avail.capacity_pct,
        notes=avail.notes,
    )


@router.post("/upload")
def upload_availability_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload availability data from CSV"""

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
                # Parse row
                candidate_email = row.get("email", "").strip()
                avail_from_str = row.get("available_from", "").strip()
                capacity_pct_str = row.get("capacity_pct", "").strip()
                notes = row.get("notes", "").strip()

                if not candidate_email or not avail_from_str or not capacity_pct_str:
                    errors.append(f"Row {row_num}: Missing required fields")
                    continue

                # Find candidate by email
                candidate = db.query(Candidate).filter(Candidate.email == candidate_email).first()
                if not candidate:
                    errors.append(f"Row {row_num}: Candidate not found: {candidate_email}")
                    continue

                # Parse date and capacity
                avail_date = date.fromisoformat(avail_from_str)
                capacity_pct = int(capacity_pct_str)

                # Upsert availability
                existing = (
                    db.query(Availability)
                    .filter(
                        Availability.candidate_id == candidate.id,
                        Availability.available_from == avail_date,
                    )
                    .first()
                )

                if existing:
                    existing.capacity_pct = capacity_pct
                    existing.notes = notes or existing.notes
                    updated += 1
                else:
                    avail = Availability(
                        candidate_id=candidate.id,
                        available_from=avail_date,
                        capacity_pct=capacity_pct,
                        notes=notes,
                    )
                    db.add(avail)
                    created += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        db.commit()

        return {
            "created": created,
            "updated": updated,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"CSV upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
