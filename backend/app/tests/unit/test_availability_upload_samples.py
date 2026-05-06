"""Synthetic sample tests for availability CSV upload flow."""
from io import BytesIO

from fastapi import UploadFile

from app.api.v1.availability import upload_availability_csv
from app.models import Agent, Candidate, Document


def _seed_candidate(db_session, email: str, name: str = "Test User") -> Candidate:
    agent = db_session.query(Agent).filter(Agent.id == "staffing").first()
    if not agent:
        agent = Agent(id="staffing", name="Staffing")
        db_session.add(agent)
        db_session.flush()

    doc = Document(
        agent_id=agent.id,
        document_type="resume",
        filename=f"{name}.pdf",
        mime_type="application/pdf",
        sha256=f"hash-{email}",
        ocr=False,
        version=1,
    )
    db_session.add(doc)
    db_session.flush()

    candidate = Candidate(
        document_id=doc.id,
        name=name,
        email=email,
        phone="+15551234567",
        location="Remote",
    )
    db_session.add(candidate)
    db_session.commit()
    return candidate


def test_upload_availability_csv_with_three_synthetic_rows(db_session):
    """Validates created, updated, and missing-candidate rows with synthetic data."""
    _seed_candidate(db_session, "alice@example.com", "Alice")
    _seed_candidate(db_session, "bob@example.com", "Bob")

    csv_content = """email,available_from,available_to,capacity_pct,notes
alice@example.com,2026-04-15,2026-05-01,60,Initial allocation
alice@example.com,2026-04-15,2026-05-10,80,Updated allocation
missing@example.com,2026-04-20,,50,Missing candidate
"""

    upload = UploadFile(
        filename="availability.csv",
        file=BytesIO(csv_content.encode("utf-8")),
    )

    result = upload_availability_csv(file=upload, _user={"permissions": ["manage:availability"]}, db=db_session)

    assert result["created"] == 1
    assert result["updated"] == 1
    assert len(result["errors"]) == 1
    assert "Candidate not found: missing@example.com" in result["errors"][0]
