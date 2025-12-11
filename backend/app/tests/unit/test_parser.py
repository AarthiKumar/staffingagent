"""Tests for resume parser"""
import pytest

from app.services.parsing.resume_parser import ResumeParser


def test_extract_name(sample_resume_text):
    """Test name extraction"""
    parser = ResumeParser()
    parsed = parser.parse(sample_resume_text.encode(), "text/plain", False)

    assert parsed["name"] == "John Doe"


def test_extract_email(sample_resume_text):
    """Test email extraction"""
    parser = ResumeParser()
    parsed = parser.parse(sample_resume_text.encode(), "text/plain", False)

    assert parsed["email"] == "john.doe@example.com"


def test_extract_location(sample_resume_text):
    """Test location extraction"""
    parser = ResumeParser()
    parsed = parser.parse(sample_resume_text.encode(), "text/plain", False)

    assert "San Francisco" in parsed["location"] or parsed["location"] is not None


def test_extract_skills(sample_resume_text):
    """Test skills extraction"""
    parser = ResumeParser()
    parsed = parser.parse(sample_resume_text.encode(), "text/plain", False)

    skills = parsed["skills"]
    assert "python" in skills
    assert "kubernetes" in skills
    assert "docker" in skills
    assert "terraform" in skills


def test_extract_experience(sample_resume_text):
    """Test experience extraction"""
    parser = ResumeParser()
    parsed = parser.parse(sample_resume_text.encode(), "text/plain", False)

    experience = parsed["experience"]
    assert len(experience) >= 2

    # Check first job
    first_job = experience[0]
    assert "DevOps" in first_job["role"] or "TechCorp" in first_job["org"]


def test_extract_certifications(sample_resume_text):
    """Test certifications extraction"""
    parser = ResumeParser()
    parsed = parser.parse(sample_resume_text.encode(), "text/plain", False)

    certs = parsed["certifications"]
    assert len(certs) >= 2
    assert any("AWS" in cert for cert in certs)
    assert any("Kubernetes" in cert for cert in certs)
