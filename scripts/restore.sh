#!/bin/bash
# Restore script for Staffing Agent

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/staffing_db_20250101_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/staffing}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from $BACKUP_FILE..."
echo "WARNING: This will drop and recreate the database!"
read -p "Continue? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Drop and recreate database
echo "Dropping database..."
psql "$DB_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Restore from backup
echo "Restoring database..."
gunzip -c "$BACKUP_FILE" | psql "$DB_URL"

echo "Restore completed successfully"
