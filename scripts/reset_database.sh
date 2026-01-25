#!/bin/bash
# Reset database - drops and recreates everything

set -e

# Parse command line arguments
FORCE=0
while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--force)
      FORCE=1
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-f|--force]"
      exit 1
      ;;
  esac
done

# Load DATABASE_URL from .env if it exists
if [ -f "$(dirname "$0")/../backend/.env" ]; then
  source "$(dirname "$0")/../backend/.env"
fi

# Parse DATABASE_URL or use defaults
if [ -n "$DATABASE_URL" ]; then
  # Extract components from DATABASE_URL
  # Format: postgresql+psycopg://user:pass@host:port/dbname
  DB_URL_REGEX="postgresql.*://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)"
  if [[ $DATABASE_URL =~ $DB_URL_REGEX ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASS="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
    echo "📋 Parsed from DATABASE_URL: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
  else
    echo "⚠️  Could not parse DATABASE_URL, using defaults"
    DATABASE_URL=""
  fi
fi

# Fallback to defaults if DATABASE_URL not set or couldn't be parsed
if [ -z "$DATABASE_URL" ]; then
  DB_NAME="${DB_NAME:-staffing}"
  DB_USER="${DB_USER:-postgres}"
  DB_PASS="${DB_PASS:-postgres}"
  DB_HOST="${DB_HOST:-localhost}"
  DB_PORT="${DB_PORT:-5432}"
  echo "📋 Using defaults: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
fi

# Confirm action
if [ $FORCE -eq 0 ]; then
  echo ""
  echo "⚠️  WARNING: This will DELETE ALL DATA in the '$DB_NAME' database!"
  echo "Press Ctrl+C to cancel, or Enter to continue..."
  read
fi

echo ""
echo "🔌 Terminating active connections to $DB_NAME..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
" 2>/dev/null || echo "No active connections found"

echo "🗑️  Dropping database '$DB_NAME'..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "🆕 Creating fresh database '$DB_NAME'..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

echo "📦 Running alembic migrations..."
cd "$(dirname "$0")/../backend"
alembic upgrade head

echo ""
echo "✅ Database reset complete!"
echo ""
echo "📊 Database info:"
echo "   Host: $DB_HOST:$DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""
echo "Next steps:"
echo "1. Restart your backend server"
echo "2. Upload CVs to test the new setup"
echo ""
