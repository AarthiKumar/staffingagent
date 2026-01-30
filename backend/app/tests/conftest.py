"""Pytest configuration and fixtures"""
import sys
from pathlib import Path

# Add backend directory to Python path so 'app' module can be imported
# This handles cases where pytest doesn't pick up pythonpath config
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing"""
    return """
John Doe
San Francisco, CA
john.doe@example.com

SUMMARY
Senior DevOps Engineer with 5+ years of experience in cloud infrastructure and automation.

SKILLS
Python, Kubernetes, Docker, Terraform, AWS, Jenkins, Ansible, Linux

EXPERIENCE
Senior DevOps Engineer
TechCorp Inc
2020 - Present
• Led migration of 50+ services to Kubernetes on AWS EKS
• Implemented CI/CD pipelines using Jenkins and GitLab CI
• Reduced infrastructure costs by 30% through optimization

DevOps Engineer
StartupCo
2018 - 2020
• Built automated deployment pipelines using Terraform and Ansible
• Managed AWS infrastructure for high-traffic applications

EDUCATION
B.S. Computer Science, University of California, 2017

CERTIFICATIONS
AWS Certified DevOps Engineer - Professional
Certified Kubernetes Administrator (CKA)
"""
