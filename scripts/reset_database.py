#!/usr/bin/env python3
"""Reset database - delete all data and recreate tables

This script:
1. Drops all tables
2. Recreates them using Alembic migrations
3. Optionally loads sample data

Usage:
    python scripts/reset_database.py [--confirm]

WARNING: This will DELETE ALL DATA in the database!
"""

import os
import sys
from pathlib import Path

# Add backend to path and change to backend directory
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))
os.chdir(str(backend_path))


def reset_database(confirm: bool = False):
    """Reset the database"""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from app.core.config import settings
    from app.db.session import engine

    print("=" * 80)
    print("DATABASE RESET")
    print("=" * 80)
    print()
    print(f"Database: {settings.database_url}")
    print()

    if not confirm:
        print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
        print()
        response = input("Are you sure you want to continue? Type 'DELETE ALL DATA' to confirm: ")

        if response != "DELETE ALL DATA":
            print("Cancelled.")
            return 1

    print()
    print("Step 1: Dropping all tables...")

    try:
        with engine.connect() as conn:
            # Drop all tables
            conn.execute(text("""
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO postgres;
                GRANT ALL ON SCHEMA public TO public;
            """))
            conn.commit()

        print("✓ All tables dropped")
    except Exception as e:
        print(f"✗ Error dropping tables: {e}")
        return 1

    print()
    print("Step 2: Running migrations...")

    try:
        # Run Alembic migrations
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        print("✓ Migrations completed")
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        return 1

    print()
    print("=" * 80)
    print("✅ DATABASE RESET COMPLETE")
    print("=" * 80)
    print()
    print("The database has been reset and is ready for use.")
    print()

    return 0


def main():
    """Main entry point"""
    confirm = "--confirm" in sys.argv

    try:
        return reset_database(confirm)
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
