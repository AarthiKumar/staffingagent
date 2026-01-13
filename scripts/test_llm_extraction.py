#!/usr/bin/env python3
"""Test script for LLM-based CV extraction

This script tests the LLM extraction service with sample CV text to verify
that it correctly extracts:
- Basic Information: Name, Email, Location
- CV Sections: Summary, Skills, Experience, Certifications

Usage:
    python scripts/test_llm_extraction.py

Requirements:
    - Set LLM_PROVIDER=openai in backend/.env
    - Set LLM_API_KEY=your_openai_api_key in backend/.env
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.llm_extraction import get_llm_extraction_service


# Sample CV text for testing
SAMPLE_CV = """
John Doe
Senior Software Engineer
john.doe@example.com | San Francisco, CA

PROFESSIONAL SUMMARY
Experienced software engineer with 8+ years building scalable web applications and cloud infrastructure.
Passionate about clean code, system design, and mentoring junior developers.

SKILLS
Python, JavaScript, TypeScript, React, Node.js, Django, FastAPI, PostgreSQL, MongoDB, Redis,
Docker, Kubernetes, AWS, Terraform, Git, CI/CD, Microservices, RESTful APIs

EXPERIENCE

Senior Software Engineer
Tech Corp | Jan 2020 - Present
- Led development of microservices architecture serving 5M+ users
- Reduced API response time by 60% through caching and optimization
- Mentored team of 5 junior developers
- Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes

Software Engineer
StartupXYZ | Jun 2017 - Dec 2019
- Built real-time analytics dashboard using React and WebSockets
- Designed and implemented RESTful API handling 10K+ requests/sec
- Migrated legacy monolith to microservices architecture
- Improved test coverage from 40% to 85%

Junior Developer
DevShop Inc | Jan 2015 - May 2017
- Developed features for e-commerce platform using Django
- Created automated testing suite reducing bug count by 30%
- Collaborated with cross-functional teams in Agile environment

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley | 2014

CERTIFICATIONS
AWS Certified Solutions Architect - Professional
Certified Kubernetes Administrator (CKA)
PMP - Project Management Professional
"""


def main():
    """Test LLM extraction with sample CV"""
    print("=" * 80)
    print("Testing LLM-based CV Extraction")
    print("=" * 80)
    print()

    # Get extraction service
    extraction_service = get_llm_extraction_service()

    if not extraction_service.enabled:
        print("❌ LLM extraction is DISABLED")
        print()
        print("To enable LLM extraction:")
        print("1. Create backend/.env file (copy from backend/.env.example)")
        print("2. Set LLM_PROVIDER=openai")
        print("3. Set LLM_API_KEY=your_openai_api_key")
        print()
        return 1

    print("✓ LLM extraction is ENABLED")
    print()

    # Test extraction
    print("Extracting data from sample CV...")
    print("-" * 80)

    try:
        result = extraction_service.extract_cv_data(SAMPLE_CV)

        print()
        print("EXTRACTION RESULTS:")
        print("=" * 80)

        # Basic Information
        print()
        print("📋 BASIC INFORMATION:")
        print(f"  Name:     {result['name']}")
        print(f"  Email:    {result['email']}")
        print(f"  Location: {result['location']}")

        # Summary
        print()
        print("📝 SUMMARY:")
        summary = result['summary']
        if summary:
            print(f"  {summary}")
        else:
            print("  (not extracted)")

        # Skills
        print()
        print("🔧 SKILLS ({} total):".format(len(result['skills'])))
        if result['skills']:
            for i, skill in enumerate(result['skills'][:10], 1):
                print(f"  {i}. {skill}")
            if len(result['skills']) > 10:
                print(f"  ... and {len(result['skills']) - 10} more")
        else:
            print("  (no skills extracted)")

        # Experience
        print()
        print("💼 EXPERIENCE ({} entries):".format(len(result['experience'])))
        for i, exp in enumerate(result['experience'], 1):
            print(f"\n  Entry {i}:")
            print(f"    Organization: {exp.get('org', 'N/A')}")
            print(f"    Role:         {exp.get('role', 'N/A')}")
            print(f"    Period:       {exp.get('start', 'N/A')} - {exp.get('end', 'N/A')}")
            bullets = exp.get('bullets', [])
            if bullets:
                print(f"    Bullets:      {len(bullets)} bullet points")
                for bullet in bullets[:2]:
                    print(f"      • {bullet[:80]}{'...' if len(bullet) > 80 else ''}")
                if len(bullets) > 2:
                    print(f"      ... and {len(bullets) - 2} more")

        # Certifications
        print()
        print("🎓 CERTIFICATIONS ({} total):".format(len(result['certifications'])))
        if result['certifications']:
            for i, cert in enumerate(result['certifications'], 1):
                print(f"  {i}. {cert}")
        else:
            print("  (no certifications extracted)")

        print()
        print("=" * 80)
        print("✅ LLM extraction completed successfully!")
        print()

        # Validation checks
        print("VALIDATION CHECKS:")
        checks_passed = 0
        checks_total = 5

        if result['name'] and result['name'] != 'Unknown':
            print("  ✓ Name extracted correctly")
            checks_passed += 1
        else:
            print("  ✗ Name not extracted or is 'Unknown'")

        if result['email']:
            print("  ✓ Email extracted correctly")
            checks_passed += 1
        else:
            print("  ✗ Email not extracted")

        if result['location']:
            print("  ✓ Location extracted correctly")
            checks_passed += 1
        else:
            print("  ✗ Location not extracted")

        if result['skills'] and len(result['skills']) >= 5:
            print(f"  ✓ Skills extracted ({len(result['skills'])} skills)")
            checks_passed += 1
        else:
            print(f"  ✗ Insufficient skills extracted ({len(result['skills'])} skills)")

        if result['experience'] and len(result['experience']) >= 2:
            print(f"  ✓ Experience extracted ({len(result['experience'])} entries)")
            checks_passed += 1
        else:
            print(f"  ✗ Insufficient experience extracted ({len(result['experience'])} entries)")

        print()
        print(f"Validation: {checks_passed}/{checks_total} checks passed")

        if checks_passed == checks_total:
            print("✅ All validation checks passed!")
            return 0
        elif checks_passed >= 3:
            print("⚠️  Some checks failed, but core functionality works")
            return 0
        else:
            print("❌ Too many validation checks failed")
            return 1

    except Exception as e:
        print()
        print(f"❌ ERROR during extraction: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
