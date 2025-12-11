#!/bin/bash
# Weekly backup script for Staffing Agent

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/staffing}"

echo "Starting backup at $TIMESTAMP"

mkdir -p "$BACKUP_DIR"

# Backup Postgres database
echo "Backing up database..."
pg_dump "$DB_URL" | gzip > "$BACKUP_DIR/staffing_db_$TIMESTAMP.sql.gz"

# Backup MinIO files (if using MinIO)
if command -v mc &> /dev/null; then
    echo "Backing up MinIO files..."
    mc mirror local-minio/originals "$BACKUP_DIR/originals_$TIMESTAMP/"
fi

# Clean up old backups (keep last 30 days)
find "$BACKUP_DIR" -name "staffing_db_*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "originals_*" -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true

echo "Backup completed: $BACKUP_DIR/staffing_db_$TIMESTAMP.sql.gz"
