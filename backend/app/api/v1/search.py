"""Search endpoints"""
import time
import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import require_permission, PERM_SEARCH_CANDIDATES, PERM_VIEW_CANDIDATES
from app.db.session import get_db
from app.models import Candidate, Availability, MetricsSearch
from app.services.ranking import RankingService
from app.services.rerank import get_rerank_service
from app.services.search import SearchService
from app.telemetry.metrics import metrics

logger = get_logger(__name__)

router = APIRouter()


class SearchFilters(BaseModel):
    required_skills: Optional[List[str]] = None
    required_certs: Optional[List[str]] = None
    min_years: Optional[Dict[str, int]] = None
    min_experience_years: Optional[float] = None
    location: Optional[str] = None
    availability_from: Optional[str] = None
    capacity_pct_min: Optional[int] = None


class SearchRequest(BaseModel):
    agent_id: str
    filters: SearchFilters
    text: Optional[str] = None
    use_llm_rerank: bool = False
    top_k: int = 50
    min_score: float = 0.8


class AvailabilityInfo(BaseModel):
    from_date: Optional[str]
    capacity_pct: Optional[int]


class WhyInfo(BaseModel):
    skills: List[str]
    certs: List[str]
    snippets: List[Dict[str, Any]]


class SearchResultItem(BaseModel):
    candidate_id: str
    name: str
    updated: str
    availability: Optional[AvailabilityInfo]
    years_experience: Optional[float]
    score: float
    why: WhyInfo


class SearchResponse(BaseModel):
    query_id: str
    flags: Dict[str, bool]
    results: List[SearchResultItem]


@router.post("/", response_model=SearchResponse)
def search_candidates(
    req: SearchRequest,
    _user: dict = Depends(require_permission(PERM_SEARCH_CANDIDATES)),
    db: Session = Depends(get_db),
):
    """Search for candidates with filters and optional semantic query"""

    start_time = time.time()
    query_id = str(uuid.uuid4())

    # Convert filters to dict
    filters_dict = req.filters.model_dump(exclude_none=True)

    # Execute search
    search_service = SearchService(db, req.agent_id)
    results = search_service.search(
        query_text=req.text,
        filters=filters_dict,
        top_k=req.top_k,
    )

    # Get sections for ranking and explanation
    sections_map = {}
    for result in results:
        sections = search_service.get_sections_for_candidate(result["candidate_id"])
        sections_map[result["candidate_id"]] = sections

    # Rank results
    ranking_service = RankingService(req.agent_id)
    results = ranking_service.rank_results(results, filters_dict, sections_map)

    # Add explanations
    for result in results:
        sections = sections_map[result["candidate_id"]]
        result["why"] = ranking_service.build_explanation(result, filters_dict, sections)

    # Optional LLM reranking
    reranked = False
    if req.use_llm_rerank:
        rerank_service = get_rerank_service(req.agent_id)
        results, reranked = rerank_service.rerank(results, req.text or "", filters_dict)

    # Confidence score cut-off (default 80%)
    results = [r for r in results if r.get("score", 0.0) >= req.min_score]

    # Build response
    response_results = []
    for result in results:
        candidate: Candidate = result["candidate"]

        # Get availability
        avail = (
            db.query(Availability)
            .filter(Availability.candidate_id == candidate.id)
            .order_by(Availability.available_from.asc())
            .first()
        )

        avail_info = None
        if avail:
            avail_info = AvailabilityInfo(
                from_date=avail.available_from.isoformat(),
                capacity_pct=avail.capacity_pct,
            )

        why_info = WhyInfo(
            skills=result["why"].get("skills", []),
            certs=result["why"].get("certs", []),
            snippets=result["why"].get("snippets", []),
        )

        response_results.append(
            SearchResultItem(
                candidate_id=str(candidate.id),
                name=candidate.name,
                updated=candidate.updated_at.isoformat(),
                availability=avail_info,
                years_experience=candidate.years_experience,
                score=result["score"],
                why=why_info,
            )
        )

    # Log metrics
    elapsed_ms = int((time.time() - start_time) * 1000)
    metrics.track_search(req.agent_id, len(response_results))
    metrics.track_request(req.agent_id, "/search", 200, elapsed_ms / 1000.0)

    # Store search metrics
    search_metric = MetricsSearch(
        query_id=uuid.UUID(query_id),
        use_llm=reranked,
        p95_ms=elapsed_ms,
        results_count=len(response_results),
        zero_result=(len(response_results) == 0),
    )
    db.add(search_metric)
    db.commit()

    return SearchResponse(
        query_id=query_id,
        flags={"reranked": reranked},
        results=response_results,
    )


@router.get("/candidates/{candidate_id}")
def get_candidate_detail(
    candidate_id: str,
    _user: dict = Depends(require_permission(PERM_VIEW_CANDIDATES)),
    db: Session = Depends(get_db),
):
    """Get detailed candidate information"""

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get availability
    avail_records = (
        db.query(Availability)
        .filter(Availability.candidate_id == candidate.id)
        .order_by(Availability.available_from.asc())
        .all()
    )

    # Get sections
    from app.models import Section, Document
    sections = (
        db.query(Section)
        .join(Document)
        .filter(Document.id == candidate.document_id)
        .all()
    )

    # Extract top skills
    skills_sections = [s for s in sections if s.type == "skills"]
    top_skills = []
    if skills_sections:
        skills_text = skills_sections[0].text
        top_skills = [s.strip() for s in skills_text.split(",")[:10]]

    # Extract certifications
    cert_sections = [s for s in sections if s.type == "certifications"]
    certifications = []
    if cert_sections:
        certifications = cert_sections[0].text.split("\n")[:5]

    return {
        "candidate_id": str(candidate.id),
        "name": candidate.name,
        "email": candidate.email,
        "location": candidate.location,
        "updated": candidate.updated_at.isoformat(),
        "top_skills": top_skills,
        "certifications": certifications,
        "availability": [
            {
                "from": a.available_from.isoformat(),
                "capacity_pct": a.capacity_pct,
                "notes": a.notes,
            }
            for a in avail_records
        ],
        "sections": [
            {
                "type": s.type,
                "text": s.text[:500],
            }
            for s in sections
            if s.type in ("summary", "experience")
        ][:5],
    }
