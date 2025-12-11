"""Tests for ranking service"""
from datetime import datetime, timedelta
import pytest

from app.models import Section, Candidate
from app.services.ranking import RankingService


class MockCandidate:
    """Mock candidate for testing"""
    def __init__(self, days_ago=0):
        self.updated_at = datetime.utcnow() - timedelta(days=days_ago)


def test_compute_skills_score():
    """Test skills match scoring"""
    service = RankingService("staffing")

    sections = [
        Section(type="skills", text="python, kubernetes, terraform"),
    ]

    score = service._compute_skills_score(sections, ["python", "kubernetes"])
    assert score == 1.0  # All required skills matched

    score = service._compute_skills_score(sections, ["python", "java"])
    assert score == 0.5  # Half matched


def test_compute_cert_score():
    """Test certification match scoring"""
    service = RankingService("staffing")

    sections = [
        Section(type="certifications", text="AWS DevOps Professional\nCKA"),
    ]

    score = service._compute_cert_score(sections, ["aws devops professional"])
    assert score == 1.0

    score = service._compute_cert_score(sections, ["aws devops professional", "gcp"])
    assert score == 0.5


def test_compute_recency_score():
    """Test recency scoring"""
    service = RankingService("staffing")

    recent_candidate = MockCandidate(days_ago=10)
    score = service._compute_recency_score(recent_candidate)
    assert score > 0.95

    old_candidate = MockCandidate(days_ago=300)
    score = service._compute_recency_score(old_candidate)
    assert score < 0.5
