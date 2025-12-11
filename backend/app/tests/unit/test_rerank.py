"""Tests for rerank service"""
import pytest

from app.services.rerank import RerankService


class MockCandidate:
    """Mock candidate for testing"""
    def __init__(self, name):
        self.name = name
        self.location = "Test City"


def test_rerank_fallback_when_disabled():
    """Test that rerank returns original results when disabled"""
    service = RerankService("staffing")
    service.enabled = False

    results = [
        {"candidate": MockCandidate("A"), "score": 0.9, "why": {}},
        {"candidate": MockCandidate("B"), "score": 0.8, "why": {}},
    ]

    reranked, flag = service.rerank(results, "test query", {})

    assert flag is False
    assert reranked == results


def test_build_evidence():
    """Test building safe evidence for LLM"""
    service = RerankService("staffing")

    results = [
        {
            "candidate": MockCandidate("John Doe"),
            "score": 0.9,
            "why": {
                "skills": ["python", "kubernetes"],
                "certs": ["aws"],
                "snippets": [{"text": "Led migration to Kubernetes"}],
            },
        }
    ]

    evidence = service._build_evidence(results, {})

    assert len(evidence) == 1
    assert evidence[0]["name"] == "John Doe"
    assert evidence[0]["matched_skills"] == ["python", "kubernetes"]
    assert evidence[0]["matched_certs"] == ["aws"]
    assert "Led migration" in evidence[0]["snippets"][0]
