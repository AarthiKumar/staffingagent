"""Search service with pgvector KNN and SQL filters"""
from typing import Any, Dict, List, Optional
from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Candidate, Document, Embedding, Section, Availability
from app.services.embeddings import get_embeddings_service

logger = get_logger(__name__)


class SearchService:
    """Handle semantic search with filters"""

    def __init__(self, db: Session, agent_id: str):
        self.db = db
        self.agent_id = agent_id
        self.embeddings_service = get_embeddings_service()

    def search(
        self,
        query_text: Optional[str],
        filters: Dict[str, Any],
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """Execute search with filters and optional semantic query"""

        # Step 1: Apply SQL hard filters
        candidate_ids = self._apply_filters(filters)

        if not candidate_ids:
            logger.info("No candidates match filters")
            return []

        # Step 2: Semantic search if query text provided
        if query_text:
            results = self._semantic_search(query_text, candidate_ids, top_k)
        else:
            # Return filtered candidates without semantic ranking
            results = self._get_candidates_by_ids(candidate_ids[:top_k])

        return results

    def _apply_filters(self, filters: Dict[str, Any]) -> List[str]:
        """Apply SQL filters and return matching candidate IDs"""
        normalized_skills = self._normalize_csv_values(filters.get("required_skills", []))
        normalized_certs = self._normalize_csv_values(filters.get("required_certs", []))

        # Build query for candidates
        query = select(Candidate.id).join(Document).where(Document.agent_id == self.agent_id)

        # Required skills filter (via sections)
        # Comma-separated values are treated as OR (match any provided skill).
        if normalized_skills:
            skill_conditions = [
                func.lower(Section.text).contains(skill.lower())
                for skill in normalized_skills
            ]
            query = query.where(
                Candidate.id.in_(
                    select(Candidate.id)
                    .join(Document)
                    .join(Section)
                    .where(
                        and_(
                            Document.agent_id == self.agent_id,
                            or_(*skill_conditions),
                        )
                    )
                )
            )

        # Required certifications filter
        # Comma-separated values are treated as OR (match any provided cert).
        if normalized_certs:
            cert_conditions = [
                func.lower(Section.text).contains(cert.lower())
                for cert in normalized_certs
            ]
            query = query.where(
                Candidate.id.in_(
                    select(Candidate.id)
                    .join(Document)
                    .join(Section)
                    .where(
                        and_(
                            Document.agent_id == self.agent_id,
                            Section.type == "certifications",
                            or_(*cert_conditions),
                        )
                    )
                )
            )

        # Minimum years of experience filter
        min_experience_years = filters.get("min_experience_years")
        if min_experience_years is not None:
            query = query.where(Candidate.years_experience >= float(min_experience_years))

        # Location filter
        location = filters.get("location")
        if location:
            query = query.where(func.lower(Candidate.location).contains(location.lower()))

        # Availability filter
        availability_from = filters.get("availability_from")
        capacity_pct_min = filters.get("capacity_pct_min")
        if availability_from or capacity_pct_min:
            avail_query = select(Availability.candidate_id)
            if availability_from:
                if isinstance(availability_from, str):
                    avail_date = date.fromisoformat(availability_from)
                else:
                    avail_date = availability_from
                avail_query = avail_query.where(Availability.available_from <= avail_date)
            if capacity_pct_min:
                avail_query = avail_query.where(Availability.capacity_pct >= capacity_pct_min)

            query = query.where(Candidate.id.in_(avail_query))

        # Execute query
        result = self.db.execute(query).scalars().all()
        unique_ids = []
        seen = set()
        for cid in result:
            cid_str = str(cid)
            if cid_str in seen:
                continue
            seen.add(cid_str)
            unique_ids.append(cid_str)
        return unique_ids

    def _semantic_search(
        self, query_text: str, candidate_ids: List[str], top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using pgvector KNN"""
        # Generate query embedding
        query_embedding = self.embeddings_service.embed_single(query_text, self.agent_id)

        # pgvector KNN search with grouping by document_id
        # We use cosine distance: 1 - cosine_similarity
        # Group by document_id to avoid duplicates (one candidate per document with max similarity)
        subquery = (
            select(
                Embedding.document_id,
                func.max(1 - Embedding.vector.cosine_distance(query_embedding)).label("max_similarity"),
            )
            .join(Document)
            .where(
                and_(
                    Document.agent_id == self.agent_id,
                    Document.id.in_(
                        select(Document.id).join(Candidate).where(Candidate.id.in_(candidate_ids))
                    ),
                )
            )
            .group_by(Embedding.document_id)
            .order_by(text("max_similarity DESC"))
            .limit(top_k)
        )

        results = self.db.execute(subquery).all()

        # Build result dictionaries
        output = []
        for doc_id, cosine_sim in results:
            candidate = (
                self.db.query(Candidate)
                .join(Document)
                .where(Document.id == doc_id)
                .first()
            )
            if candidate:
                output.append({
                    "candidate_id": str(candidate.id),
                    "document_id": str(doc_id),
                    "cosine_similarity": float(cosine_sim),
                    "candidate": candidate,
                })

        return output

    def _get_candidates_by_ids(self, candidate_ids: List[str]) -> List[Dict[str, Any]]:
        """Get candidates by IDs without semantic ranking"""
        deduped_ids = list(dict.fromkeys(candidate_ids))
        output = []
        for cid in deduped_ids:
            candidate_uuid = self._to_uuid(cid)
            candidate = self.db.query(Candidate).filter(Candidate.id == (candidate_uuid or cid)).first()
            if candidate:
                output.append({
                    "candidate_id": str(candidate.id),
                    "document_id": str(candidate.document_id),
                    # Without semantic query text, treat filtered candidates as
                    # baseline high-confidence matches for scoring purposes.
                    "cosine_similarity": 1.0,
                    "candidate": candidate,
                })
        return output

    def get_sections_for_candidate(self, candidate_id: str) -> List[Section]:
        """Get all sections for a candidate"""
        candidate_uuid = self._to_uuid(candidate_id)
        candidate = self.db.query(Candidate).filter(Candidate.id == (candidate_uuid or candidate_id)).first()
        if not candidate:
            return []

        sections = (
            self.db.query(Section)
            .join(Document)
            .where(Document.id == candidate.document_id)
            .all()
        )
        return sections

    @staticmethod
    def _normalize_csv_values(values: Any) -> List[str]:
        """Normalize list/string filter values and split comma-separated tokens."""
        if values is None:
            return []
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            return []

        normalized: List[str] = []
        for value in values:
            if value is None:
                continue
            for token in str(value).split(","):
                cleaned = token.strip()
                if cleaned:
                    normalized.append(cleaned)
        return list(dict.fromkeys(normalized))

    @staticmethod
    def _to_uuid(value: Any):
        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            return None
