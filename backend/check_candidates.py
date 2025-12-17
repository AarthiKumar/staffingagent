#!/usr/bin/env python3
"""Quick diagnostic script to check candidates in database"""
import sys
from app.db.session import SessionLocal
from app.models import Candidate, Document

def main():
    db = SessionLocal()
    try:
        # Count candidates
        candidate_count = db.query(Candidate).count()
        print(f"Total candidates in database: {candidate_count}")

        if candidate_count == 0:
            print("\n❌ No candidates found in database")

            # Check if documents exist
            doc_count = db.query(Document).count()
            print(f"Total documents in database: {doc_count}")

            if doc_count == 0:
                print("\n⚠️  No documents uploaded yet")
                print("Please upload CVs via http://localhost:5173/upload")
            else:
                print("\n⚠️  Documents exist but no candidates created")
                print("This indicates an issue with the ingestion process")
        else:
            print(f"\n✅ Found {candidate_count} candidates:")
            candidates = db.query(Candidate).limit(10).all()
            for c in candidates:
                print(f"\n  ID: {c.id}")
                print(f"  Name: {c.name}")
                print(f"  Email: {c.email or 'N/A'}")
                print(f"  Location: {c.location or 'N/A'}")
                print(f"  Updated: {c.updated_at}")

    except Exception as e:
        print(f"\n❌ Database error: {e}")
        print("\nMake sure:")
        print("1. Docker containers are running: docker-compose ps")
        print("2. Database migrations are applied: cd backend && alembic upgrade head")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
