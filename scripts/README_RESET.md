# Database Reset Scripts

Three options for resetting your database, depending on your setup.

## Quick Start

**Don't know your setup? Try this first:**

```bash
# Option 1: Truncate all tables (recommended - fastest, safest)
./scripts/reset_db_sql.sh
```

## The Options

### Option 1: SQL Truncate (Recommended) ⭐

**File:** `reset_db_sql.sh`

**What it does:**
- Truncates (empties) all tables
- Keeps schema and indexes intact
- Fast and reliable

**Requirements:**
- `psql` command must be installed
- `DATABASE_URL` set in environment or `backend/.env` file

**Usage:**
```bash
./scripts/reset_db_sql.sh          # Interactive (asks for confirmation)
./scripts/reset_db_sql.sh --force  # Skip confirmation
```

**Best for:** Most users, fastest option

---

### Option 2: Simple Python Method

**File:** `reset_db_simple.py`

**What it does:**
- Uses `alembic downgrade base` to drop tables
- Uses `alembic upgrade head` to recreate tables
- Works through Python/alembic

**Requirements:**
- Python environment with alembic installed
- Working alembic configuration

**Usage:**
```bash
./scripts/reset_db_simple.py          # Interactive
./scripts/reset_db_simple.py --force  # Skip confirmation
```

**Best for:** When you want to use existing alembic tooling

---

### Option 3: Full Database Drop/Recreate

**Files:** `reset_database.sh` or `reset_database.py`

**What it does:**
- Drops entire database
- Creates fresh database
- Runs all migrations

**Requirements:**
- For `.sh`: psql command + DATABASE_URL
- For `.py`: Python with SQLAlchemy + sqlalchemy-utils

**Usage:**
```bash
./scripts/reset_database.sh --force
# OR
./scripts/reset_database.py --force
```

**Best for:** Complete fresh start, but slowest option

---

## Troubleshooting

### "Connection refused" error
Your database isn't running on localhost:5432. Set `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql+psycopg://user:pass@host:port/dbname"
./scripts/reset_db_sql.sh
```

Or create `backend/.env` file:
```
DATABASE_URL=postgresql+psycopg://user:pass@host:port/dbname
```

### "psql: command not found"
Install PostgreSQL client:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# Mac
brew install postgresql
```

Or use the Python methods instead.

### "alembic: command not found"
Activate your Python virtual environment first:
```bash
source venv/bin/activate  # or wherever your venv is
./scripts/reset_db_simple.py
```

---

## What Gets Deleted?

All scripts delete:
- ✅ All candidate records
- ✅ All documents
- ✅ All CV sections
- ✅ All embeddings
- ✅ All availability records

The schema (table structure) is preserved or recreated.

## After Reset

1. Restart your backend server (if it's running)
2. Upload CVs to populate fresh data
3. Test searches to verify everything works
