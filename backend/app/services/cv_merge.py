"""CV merge service for handling duplicate candidates"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Candidate, Document, Section

logger = get_logger(__name__)


class CVMergeService:
    """Handle CV duplicate detection and merging"""

    def __init__(self, db: Session):
        self.db = db

    def find_duplicate(
        self, name: str, email: Optional[str], phone: Optional[str]
    ) -> Optional[Candidate]:
        """
        Find existing candidate by email or phone (primary keys) or name+location

        Args:
            name: Candidate name
            email: Email address
            phone: Phone number

        Returns:
            Existing candidate if found, None otherwise
        """
        # Try email first (most reliable)
        if email:
            existing = self.db.query(Candidate).filter(Candidate.email == email).first()
            if existing:
                logger.info(f"Found duplicate by email: {email}")
                return existing

        # Try phone (also reliable)
        if phone:
            existing = self.db.query(Candidate).filter(Candidate.phone == phone).first()
            if existing:
                logger.info(f"Found duplicate by phone: {phone}")
                return existing

        # Fallback: try name match (less reliable, so we don't use this alone)
        # Only use name if we don't have email or phone
        if not email and not phone:
            existing = self.db.query(Candidate).filter(Candidate.name.ilike(f"%{name}%")).first()
            if existing:
                logger.info(f"Found potential duplicate by name: {name}")
                return existing

        return None

    def create_merge_proposal(
        self,
        existing_candidate: Candidate,
        new_parsed_data: Dict[str, Any],
        new_sections: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Create a merge proposal comparing existing and new candidate data

        Args:
            existing_candidate: Existing candidate in database
            new_parsed_data: Newly parsed candidate data
            new_sections: Newly extracted CV sections

        Returns:
            Merge proposal with comparison
        """
        # Get existing sections
        existing_doc = existing_candidate.document
        existing_sections_db = (
            self.db.query(Section)
            .filter(Section.document_id == existing_doc.id)
            .all()
        )

        existing_sections = []
        for sec in existing_sections_db:
            existing_sections.append({
                "type": sec.type,
                "text": sec.text,
            })

        # Build comparison
        proposal = {
            "duplicate_found": True,
            "existing_candidate_id": str(existing_candidate.id),
            "existing_data": {
                "name": existing_candidate.name,
                "email": existing_candidate.email,
                "phone": existing_candidate.phone,
                "location": existing_candidate.location,
                "sections": existing_sections,
            },
            "new_data": {
                "name": new_parsed_data.get("name"),
                "email": new_parsed_data.get("email"),
                "phone": new_parsed_data.get("phone"),
                "location": new_parsed_data.get("location"),
                "sections": new_sections,
            },
            "suggested_merge": {
                # Use most complete data
                "name": new_parsed_data.get("name") or existing_candidate.name,
                "email": new_parsed_data.get("email") or existing_candidate.email,
                "phone": new_parsed_data.get("phone") or existing_candidate.phone,
                "location": new_parsed_data.get("location") or existing_candidate.location,
                # Suggest keeping both CVs' sections
                "keep_both_cvs": True,
                "action_required": "User must review and approve merge",
            },
            "conflict_fields": self._identify_conflicts(
                existing_candidate, new_parsed_data
            ),
        }

        return proposal

    def _identify_conflicts(
        self, existing: Candidate, new_data: Dict[str, Any]
    ) -> List[str]:
        """Identify fields that have different values"""
        conflicts = []

        # Check each field
        if existing.name != new_data.get("name") and new_data.get("name"):
            conflicts.append("name")

        if existing.email != new_data.get("email") and new_data.get("email"):
            conflicts.append("email")

        if existing.phone != new_data.get("phone") and new_data.get("phone"):
            conflicts.append("phone")

        if existing.location != new_data.get("location") and new_data.get("location"):
            conflicts.append("location")

        return conflicts

    def apply_merge(
        self,
        candidate_id: UUID,
        approved_data: Dict[str, Any],
        new_document_id: UUID,
    ) -> Candidate:
        """
        Apply approved merge to existing candidate

        Args:
            candidate_id: Existing candidate ID
            approved_data: User-approved merged data
            new_document_id: ID of the new document to link

        Returns:
            Updated candidate
        """
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Update candidate with approved data
        if "name" in approved_data:
            candidate.name = approved_data["name"]

        if "email" in approved_data:
            candidate.email = approved_data["email"]

        if "phone" in approved_data:
            candidate.phone = approved_data["phone"]

        if "location" in approved_data:
            candidate.location = approved_data["location"]

        # NOTE: If keeping both CVs, the new document and sections already exist
        # and are searchable. We just need to update the candidate record.

        self.db.commit()
        self.db.refresh(candidate)

        logger.info(f"Applied merge for candidate {candidate_id}")

        return candidate


def get_cv_merge_service(db: Session) -> CVMergeService:
    """Get CV merge service"""
    return CVMergeService(db)
