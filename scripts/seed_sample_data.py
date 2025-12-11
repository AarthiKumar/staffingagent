#!/usr/bin/env python3
"""Seed sample candidate data"""
import base64
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import requests

API_BASE = "http://localhost:8000/api/v1"


def create_sample_resume(name: str, skills: list[str], certs: list[str], org: str) -> str:
    """Create a sample resume text"""
    return f"""
{name}
San Francisco, CA
{name.lower().replace(' ', '.')}@example.com

SUMMARY
Senior engineer with 5+ years of experience in cloud infrastructure and automation.

SKILLS
{', '.join(skills)}

EXPERIENCE
Senior Engineer
{org}
2020 - Present
• Led migration to cloud infrastructure
• Implemented CI/CD pipelines
• Reduced costs by 30%

Engineer
PreviousCo
2018 - 2020
• Built automated deployment systems
• Managed production infrastructure

EDUCATION
B.S. Computer Science, University of California, 2017

CERTIFICATIONS
{chr(10).join(certs)}
"""


def ingest_resume(filename: str, content: str):
    """Ingest a resume via API"""
    encoded = base64.b64encode(content.encode()).decode()
    payload = {
        "agent_id": "staffing",
        "document_type": "resume",
        "filename": filename,
        "content_base64": encoded,
        "use_ocr": False,
    }

    response = requests.post(f"{API_BASE}/ingest/", json=payload)
    response.raise_for_status()
    return response.json()


def main():
    """Seed sample data"""
    print("Seeding sample candidate data...")

    candidates = [
        {
            "name": "Alice Johnson",
            "skills": ["python", "kubernetes", "docker", "terraform", "aws"],
            "certs": ["AWS Certified DevOps Engineer - Professional", "CKA"],
            "org": "TechCorp",
        },
        {
            "name": "Bob Smith",
            "skills": ["java", "kubernetes", "jenkins", "azure", "terraform"],
            "certs": ["Azure DevOps Engineer Expert"],
            "org": "CloudCo",
        },
        {
            "name": "Carol Williams",
            "skills": ["python", "ansible", "docker", "gcp", "linux"],
            "certs": ["Google Cloud Professional DevOps Engineer"],
            "org": "StartupInc",
        },
        {
            "name": "David Brown",
            "skills": ["javascript", "typescript", "react", "node", "aws"],
            "certs": ["AWS Certified Solutions Architect"],
            "org": "WebTech",
        },
        {
            "name": "Eve Davis",
            "skills": ["python", "kubernetes", "terraform", "prometheus", "grafana"],
            "certs": ["CKA", "CKAD"],
            "org": "InfraCorp",
        },
    ]

    for candidate in candidates:
        print(f"Ingesting {candidate['name']}...")
        resume_text = create_sample_resume(
            candidate["name"],
            candidate["skills"],
            candidate["certs"],
            candidate["org"],
        )
        result = ingest_resume(f"{candidate['name']}.txt", resume_text)
        print(f"  Created candidate_id: {result['candidate_id']}")

    print(f"\n✓ Seeded {len(candidates)} candidates")


if __name__ == "__main__":
    main()
