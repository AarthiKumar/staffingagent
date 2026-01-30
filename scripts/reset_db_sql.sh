#!/bin/bash
# Reset database using raw SQL - works with any connection method

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
      shift
      ;;
  esac
done

echo "📋 Database Reset Tool (SQL Method)"
echo "=" "================================================================"
echo ""
echo "This script will TRUNCATE all tables (delete all data) but keep"
echo "the schema intact. This is faster and safer than DROP DATABASE."
echo ""

# Confirm action
if [ $FORCE -eq 0 ]; then
  echo "⚠️  WARNING: This will DELETE ALL DATA in your database!"
  echo ""
  read -p "Type 'YES' (in caps) to continue: " response
  if [ "$response" != "YES" ]; then
    echo "❌ Cancelled"
    exit 1
  fi
fi

echo ""
echo "Looking for database connection..."

# Try to get DATABASE_URL from backend/.env
if [ -f "backend/.env" ]; then
  source backend/.env
  echo "✓ Loaded from backend/.env"
elif [ -f ".env" ]; then
  source .env
  echo "✓ Loaded from .env"
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
  echo "❌ DATABASE_URL not found!"
  echo ""
  echo "Please set DATABASE_URL environment variable or create backend/.env with:"
  echo "  DATABASE_URL=postgresql+psycopg://user:pass@host:port/dbname"
  echo ""
  exit 1
fi

echo "📋 DATABASE_URL: ${DATABASE_URL//:*@/:***@}"
echo ""

# Parse DATABASE_URL
# Format: postgresql+psycopg://user:pass@host:port/dbname
if [[ $DATABASE_URL =~ postgresql.*://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
  DB_USER="${BASH_REMATCH[1]}"
  DB_PASS="${BASH_REMATCH[2]}"
  DB_HOST="${BASH_REMATCH[3]}"
  DB_PORT="${BASH_REMATCH[4]}"
  DB_NAME="${BASH_REMATCH[5]}"
else
  echo "❌ Could not parse DATABASE_URL"
  exit 1
fi

echo "📊 Connection details:"
echo "   Host: $DB_HOST:$DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# Create SQL script to truncate all tables
SQL_SCRIPT=$(cat <<'EOSQL'
-- Disable foreign key checks temporarily
SET session_replication_role = 'replica';

-- Truncate all tables
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
    LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Truncated table: %', r.tablename;
    END LOOP;
END $$;

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Show result
SELECT
    schemaname as schema,
    tablename as table,
    n_live_tup as rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY tablename;
EOSQL
)

echo "🗑️  Truncating all tables..."
echo ""

# Execute SQL
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<< "$SQL_SCRIPT"

echo ""
echo "✅ Database reset complete!"
echo ""
echo "📊 All tables have been truncated (data deleted)"
echo "   Schema and indexes remain intact"
echo ""
echo "Next steps:"
echo "1. Restart your backend server (if needed)"
echo "2. Upload CVs to populate the database"
echo ""
