import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
sys.path.append(str(REPO_ROOT / "backend"))

from app.services.parsing.resume_parser import ResumeParser  # noqa: E402


def main() -> int:
    parser = ResumeParser()
    synthetic_resume = """
    JANE DOE
    jane.doe@example.com | +1 (415) 555-1212 | San Francisco, CA

    SUMMARY:
    Product-focused software engineer with 7+ years of experience building web platforms.

    SKILLS - Python, FastAPI, React, PostgreSQL, Docker, AWS

    EXPERIENCE:
    Acme Corp - Senior Software Engineer
    Jan 2020 - Present
    • Led migration to microservices and improved uptime by 25%.
    • Built analytics dashboards used by 50+ stakeholders.

    Beta Inc - Software Engineer
    2017 - 2019
    - Developed APIs for payments processing and reconciliation.

    EDUCATION:
    B.S. Computer Science, University of Example, 2016

    CERTIFICATIONS:
    AWS Certified Solutions Architect
    """

    parsed = parser.parse(synthetic_resume.encode("utf-8"), "text/plain", use_ocr=False)

    failures = []
    if not parsed.get("summary"):
        failures.append("summary")
    if not parsed.get("skills"):
        failures.append("skills")
    if not parsed.get("experience"):
        failures.append("experience")
    if not parsed.get("education"):
        failures.append("education")
    if not parsed.get("certifications"):
        failures.append("certifications")

    if failures:
        print(f"Missing parsed sections: {', '.join(failures)}")
        return 1

    print("Parsed sections:")
    print(f"- summary: {parsed['summary'][:60]}...")
    print(f"- skills: {parsed['skills']}")
    print(f"- experience entries: {len(parsed['experience'])}")
    print(f"- education entries: {len(parsed['education'])}")
    print(f"- certifications: {parsed['certifications']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
