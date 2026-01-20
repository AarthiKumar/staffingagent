#!/usr/bin/env python3
"""
Check database status and diagnose issues
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from sqlalchemy import inspect, text
    from app.core.database import engine, SessionLocal
    from app.models.candidate import Candidate

    print("✓ Successfully imported database modules\n")

    # Check if database is accessible
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}\n")
        sys.exit(1)

    # Check if tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables in database: {', '.join(tables)}\n")

    if 'candidates' not in tables:
        print("✗ Candidates table does not exist!")
        print("   Run: cd backend && alembic upgrade head\n")
        sys.exit(1)

    print("✓ Candidates table exists\n")

    # Check if phone column exists
    columns = [col['name'] for col in inspector.get_columns('candidates')]
    print(f"Columns in candidates table: {', '.join(columns)}\n")

    if 'phone' not in columns:
        print("✗ Phone column missing!")
        print("   Run: cd backend && alembic upgrade head\n")
        sys.exit(1)

    print("✓ Phone column exists\n")

    # Check candidates count
    db = SessionLocal()
    try:
        count = db.query(Candidate).count()
        print(f"Total candidates in database: {count}\n")

        if count == 0:
            print("⚠ No candidates found in database")
            print("  This is normal if you just reset the database.")
            print("  Try uploading a CV to test.\n")
        else:
            print("Recent candidates:")
            candidates = db.query(Candidate).order_by(Candidate.updated_at.desc()).limit(5).all()
            for c in candidates:
                print(f"  - {c.name}")
                print(f"    Email: {c.email or 'N/A'}")
                print(f"    Phone: {c.phone or 'N/A'}")
                print(f"    ID: {c.id}")
                print()
    finally:
        db.close()

    print("\n✓ Database check completed successfully!")

except ImportError as e:
    print(f"✗ Missing dependencies: {e}")
    print("   Run: cd backend && pip install -r requirements.txt\n")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
