#!/bin/bash
# Reset database - drops and recreates everything

set -e

echo "⚠️  WARNING: This will DELETE ALL DATA in the staffing database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Database connection details
DB_NAME="staffing"
DB_USER="postgres"
DB_PASS="postgres"
DB_HOST="localhost"
DB_PORT="5432"

echo "🗑️  Dropping database..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "🆕 Creating fresh database..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

echo "📦 Running migrations..."
cd "$(dirname "$0")/../backend"
alembic upgrade head

echo "✅ Database reset complete!"
echo ""
echo "Next steps:"
echo "1. Restart your backend server"
echo "2. Upload CVs to test"
