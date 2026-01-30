#!/bin/bash
# Reset database for Docker-based staffing agent setup

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

echo "📋 Staffing Agent - Database Reset"
echo "=" "================================================================"
echo ""

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Database connection details from docker-compose.yml
CONTAINER_NAME="staffing-postgres"
DB_NAME="staffing"
DB_USER="postgres"
DB_PASS="postgres"

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '${CONTAINER_NAME}' not found!"
    echo ""
    echo "Starting Docker Compose services..."
    cd "$(dirname "$0")/../docker"
    docker-compose up -d postgres
    echo "✓ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  Container exists but is not running. Starting it..."
    docker start ${CONTAINER_NAME}
    echo "✓ Waiting for PostgreSQL to be ready..."
    sleep 3
fi

echo "📊 Database info:"
echo "   Container: ${CONTAINER_NAME}"
echo "   Database: ${DB_NAME}"
echo "   User: ${DB_USER}"
echo ""

# Confirm action
if [ $FORCE -eq 0 ]; then
    echo "⚠️  WARNING: This will DELETE ALL DATA in the '${DB_NAME}' database!"
    echo "   - All candidates"
    echo "   - All documents"
    echo "   - All CV sections"
    echo "   - All embeddings"
    echo "   - All availability records"
    echo ""
    read -p "Type 'YES' (in caps) to continue: " response
    if [ "$response" != "YES" ]; then
        echo "❌ Cancelled"
        exit 0
    fi
fi

echo ""
echo "🗑️  Truncating all tables..."

# Create SQL to truncate all tables
SQL_SCRIPT='
-- Disable foreign key checks temporarily
SET session_replication_role = '\''replica'\'';

-- Truncate all tables
DO $$
DECLARE
    r RECORD;
    table_count INTEGER := 0;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '\''public'\'')
    LOOP
        EXECUTE '\''TRUNCATE TABLE '\'' || quote_ident(r.tablename) || '\'' CASCADE'\'';
        table_count := table_count + 1;
        RAISE NOTICE '\''✓ Truncated: %'\'', r.tablename;
    END LOOP;
    RAISE NOTICE '\''---------------------------------'\'';
    RAISE NOTICE '\''Total tables truncated: %'\'', table_count;
END $$;

-- Re-enable foreign key checks
SET session_replication_role = '\''origin'\'';

-- Verify all tables are empty
SELECT
    schemaname as schema,
    tablename as table,
    n_live_tup as rows
FROM pg_stat_user_tables
WHERE schemaname = '\''public'\''
ORDER BY tablename;
'

# Execute SQL inside the container
docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} <<< "$SQL_SCRIPT"

echo ""
echo "✅ Database reset complete!"
echo ""
echo "📊 All data has been deleted from '${DB_NAME}'"
echo "   Schema and indexes remain intact"
echo ""
echo "Next steps:"
echo "1. Restart your backend server (if running)"
echo "2. Upload CVs to populate fresh data"
echo "3. Run searches to verify everything works"
echo ""
