#!/usr/bin/env python3
"""Reset database - drops and recreates everything using SQLAlchemy"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import argparse
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, drop_database, create_database

# Import settings to get DATABASE_URL
from app.core.config import settings


def parse_args():
    parser = argparse.ArgumentParser(description="Reset the staffing database")
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Get database URL from settings
    database_url = settings.database_url

    # Parse database name for display
    db_name = database_url.split("/")[-1]

    print(f"📋 Database URL: {database_url.replace('postgres:', '***:')}")
    print(f"📋 Database name: {db_name}")

    # Confirm action
    if not args.force:
        print()
        print(f"⚠️  WARNING: This will DELETE ALL DATA in the '{db_name}' database!")
        response = input("Type 'yes' to continue, or anything else to cancel: ")
        if response.lower() != "yes":
            print("❌ Cancelled")
            return 1

    print()

    try:
        # Check if database exists
        if database_exists(database_url):
            print(f"🔌 Terminating active connections to '{db_name}'...")

            # Connect to postgres database to terminate connections
            postgres_url = "/".join(database_url.split("/")[:-1]) + "/postgres"
            engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")

            with engine.connect() as conn:
                # Terminate active connections
                result = conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_name}'
                      AND pid <> pg_backend_pid();
                """))
                terminated = sum(1 for row in result if row[0])
                if terminated > 0:
                    print(f"   Terminated {terminated} active connection(s)")
                else:
                    print("   No active connections found")

            engine.dispose()

            print(f"🗑️  Dropping database '{db_name}'...")
            drop_database(database_url)
            print("   ✓ Database dropped")
        else:
            print(f"ℹ️  Database '{db_name}' does not exist")

        print(f"🆕 Creating fresh database '{db_name}'...")
        create_database(database_url)
        print("   ✓ Database created")

        print("📦 Running alembic migrations...")
        os.chdir(backend_path)
        exit_code = os.system("alembic upgrade head")

        if exit_code != 0:
            print("❌ Migration failed!")
            return 1

        print()
        print("✅ Database reset complete!")
        print()
        print("📊 Database info:")
        print(f"   Database: {db_name}")
        print()
        print("Next steps:")
        print("1. Restart your backend server")
        print("2. Upload CVs to test the new setup")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
