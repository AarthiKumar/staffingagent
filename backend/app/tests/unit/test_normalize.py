"""Tests for normalization service"""
import pytest
from pathlib import Path

from app.services.normalize import NormalizeService


@pytest.fixture
def normalize_service(tmp_path):
    """Create a normalize service with test data"""
    # Create test CSVs
    skills_csv = tmp_path / "skills.csv"
    skills_csv.write_text("name\npython\nkubernetes\nterraform\n")

    aliases_csv = tmp_path / "aliases.csv"
    aliases_csv.write_text("alias,canonical\nk8s,kubernetes\ntf,terraform\n")

    certs_csv = tmp_path / "certs.csv"
    certs_csv.write_text("name\naws devops professional\ncka\n")

    return NormalizeService(str(skills_csv), str(aliases_csv), str(certs_csv))


def test_normalize_skill_canonical(normalize_service):
    """Test normalizing a canonical skill"""
    result = normalize_service.normalize_skill("Python")
    assert result == "python"


def test_normalize_skill_alias(normalize_service):
    """Test normalizing an alias"""
    result = normalize_service.normalize_skill("k8s")
    assert result == "kubernetes"


def test_normalize_skills_list(normalize_service):
    """Test normalizing a list of skills"""
    skills = ["Python", "k8s", "terraform"]
    result = normalize_service.normalize_skills(skills)

    assert "python" in result
    assert "kubernetes" in result
    assert "terraform" in result


def test_compute_years_per_skill(normalize_service):
    """Test computing years of experience per skill"""
    experience = [
        {
            "org": "TechCorp",
            "role": "Engineer",
            "start": "2020",
            "end": "2023",
            "bullets": ["Worked with Python and Kubernetes"],
        }
    ]

    years = normalize_service.compute_years_per_skill(experience)
    assert years.get("python", 0) == 3.0
    assert years.get("kubernetes", 0) == 3.0
