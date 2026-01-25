#!/usr/bin/env python3
"""
Simple database reset script that uses Alembic's database connection.
Works without needing to parse DATABASE_URL or having psql installed.
"""
import sys
import subprocess
from pathlib import Path

def main():
    """Reset database using SQL commands through Alembic"""

    # Change to backend directory
    backend_dir = Path(__file__).parent.parent / "backend"

    # Check for --force flag
    force = "--force" in sys.argv or "-f" in sys.argv

    print("📋 Database Reset Tool")
    print("=" * 60)
    print()

    if not force:
        print("⚠️  WARNING: This will DELETE ALL DATA in your database!")
        print()
        response = input("Type 'YES' (in caps) to continue: ")
        if response != "YES":
            print("❌ Cancelled")
            return 1

    print()
    print("🗑️  Dropping all tables...")

    # Use alembic downgrade to drop all tables
    result = subprocess.run(
        ["alembic", "downgrade", "base"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"⚠️  Downgrade returned code {result.returncode}")
        print(result.stdout)
        print(result.stderr)
        print("Continuing anyway...")
    else:
        print("   ✓ All tables dropped")

    print()
    print("🆕 Creating fresh tables...")

    # Use alembic upgrade to recreate all tables
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ Failed to create tables!")
        print(result.stdout)
        print(result.stderr)
        return 1

    print("   ✓ All tables created")
    print()
    print("✅ Database reset complete!")
    print()
    print("📊 Your database now has:")
    print("   • Empty tables with fresh schema")
    print("   • Latest migration version")
    print()
    print("Next steps:")
    print("1. Restart your backend server (if running)")
    print("2. Upload CVs to populate the database")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
