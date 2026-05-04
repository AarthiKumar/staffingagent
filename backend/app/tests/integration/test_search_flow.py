"""Integration tests for end-to-end search flow."""
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.search import SearchFilters, SearchRequest, search_candidates
from app.models import Agent, Availability, Candidate, Document, Section
from app.models.base import Base
from app.services import search as search_module


def _seed_candidate(
    db,
    *,
    sha: str,
    name: str,
    email: str,
    years_experience: float,
    skills_text: str,
    certs_text: str,
) -> Candidate:
    doc = Document(
        sha256=sha,
        agent_id="staffing",
        document_type="resume",
        filename=f"{name}.pdf",
        mime_type="application/pdf",
        ocr=False,
        version=1,
    )
    db.add(doc)
    db.flush()

    candidate = Candidate(
        document_id=doc.id,
        name=name,
        email=email,
        phone="+15551234567",
        location="Remote",
        years_experience=years_experience,
    )
    db.add(candidate)
    db.flush()

    db.add_all(
        [
            Section(document_id=doc.id, type="skills", text=skills_text, start_idx=0, end_idx=len(skills_text)),
            Section(document_id=doc.id, type="certifications", text=certs_text, start_idx=0, end_idx=len(certs_text)),
            Section(document_id=doc.id, type="summary", text=f"{name} summary", start_idx=0, end_idx=20),
            Section(document_id=doc.id, type="experience", text=f"{name} experience", start_idx=0, end_idx=30),
        ]
    )
    db.add(
        Availability(
            candidate_id=candidate.id,
            available_from=date(2026, 4, 15),
            capacity_pct=80,
            notes="Integration test seed",
        )
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def test_search_end_to_end_filters_score_and_experience(monkeypatch):
    """End-to-end search test for comma filters + min score + years of experience."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        db.add(Agent(id="staffing", name="Staffing"))
        db.commit()

        match = _seed_candidate(
            db,
            sha="hash-match",
            name="Alice Match",
            email="alice@example.com",
            years_experience=7.5,
            skills_text="python, aws, kubernetes",
            certs_text="AWS Certified Solutions Architect",
        )
        _seed_candidate(
            db,
            sha="hash-low",
            name="Bob Low",
            email="bob@example.com",
            years_experience=2.0,
            skills_text="java, spring",
            certs_text="Oracle Certified Associate",
        )

        class _FakeEmbeddingsService:
            def embed_single(self, query_text, agent_id):
                return [0.0]

        monkeypatch.setattr(
            search_module,
            "get_embeddings_service",
            lambda: _FakeEmbeddingsService(),
        )

        req = SearchRequest(
            agent_id="staffing",
            filters=SearchFilters(
                required_skills=["python, aws"],
                min_experience_years=5.0,
            ),
            text=None,
            use_llm_rerank=False,
            top_k=50,
            min_score=0.4,
        )

        resp = search_candidates(req=req, _user={"permissions": ["search:candidates"]}, db=db)

        assert len(resp.results) == 1
        assert resp.results[0].candidate_id == str(match.id)
        assert resp.results[0].years_experience == 7.5
        assert resp.results[0].score >= 0.4
    finally:
        db.close()


def test_search_comma_separated_skills_match_any_value(monkeypatch):
    """Comma-separated skills should match candidates with any listed skill."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        db.add(Agent(id="staffing", name="Staffing"))
        db.commit()

        candidate_python = _seed_candidate(
            db,
            sha="hash-python",
            name="Python Candidate",
            email="py@example.com",
            years_experience=6.0,
            skills_text="python, flask",
            certs_text="",
        )
        candidate_aws = _seed_candidate(
            db,
            sha="hash-aws",
            name="AWS Candidate",
            email="aws@example.com",
            years_experience=6.0,
            skills_text="aws, terraform",
            certs_text="",
        )

        class _FakeEmbeddingsService:
            def embed_single(self, query_text, agent_id):
                return [0.0]

        monkeypatch.setattr(
            search_module,
            "get_embeddings_service",
            lambda: _FakeEmbeddingsService(),
        )

        req = SearchRequest(
            agent_id="staffing",
            filters=SearchFilters(required_skills=["python, aws"]),
            text=None,
            use_llm_rerank=False,
            top_k=50,
            min_score=0.8,
        )

        resp = search_candidates(req=req, _user={"permissions": ["search:candidates"]}, db=db)
        result_ids = {r.candidate_id for r in resp.results}

        assert str(candidate_python.id) in result_ids
        assert str(candidate_aws.id) in result_ids
    finally:
        db.close()
