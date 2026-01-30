# How to Reset Your Database

## Your Setup

You have a **Docker-based setup** with PostgreSQL in a container. Based on your `docker/docker-compose.yml`:

- **Container name:** `staffing-postgres`
- **Database:** `staffing`
- **User:** `postgres`
- **Password:** `postgres`
- **Port:** `5432`

---

## ⭐ RECOMMENDED: Reset with Docker (Easiest)

### Step 1: Start Docker Services

```bash
cd /home/user/staffingagent/docker
docker-compose up -d postgres
```

Wait 5-10 seconds for PostgreSQL to start.

### Step 2: Reset the Database

```bash
cd /home/user/staffingagent
./scripts/reset_db_docker.sh
```

**Or skip confirmation:**
```bash
./scripts/reset_db_docker.sh --force
```

---

## Alternative: Manual Reset via Docker

If the script doesn't work, do it manually:

### 1. Start PostgreSQL container
```bash
cd /home/user/staffingagent/docker
docker-compose up -d postgres
```

### 2. Connect to the database
```bash
docker exec -it staffing-postgres psql -U postgres -d staffing
```

### 3. Run this SQL
```sql
-- Disable foreign key checks
SET session_replication_role = 'replica';

-- Truncate all tables
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
    LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Truncated: %', r.tablename;
    END LOOP;
END $$;

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Verify (should show 0 rows for all tables)
SELECT tablename, n_live_tup as rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### 4. Exit
```
\q
```

---

## Alternative: Reset Entire Docker Volume (Nuclear Option)

**⚠️ WARNING: This deletes EVERYTHING including the database itself**

```bash
cd /home/user/staffingagent/docker

# Stop all services
docker-compose down

# Delete the database volume (COMPLETE DATA LOSS)
docker volume rm docker_postgres_data

# Start services again (creates fresh database)
docker-compose up -d postgres

# Wait for startup
sleep 10

# Run migrations to create tables
cd ../backend
alembic upgrade head
```

---

## After Reset

1. **Restart your backend server** (if it's running)
   ```bash
   # Stop current backend (Ctrl+C if running in terminal)
   # Or find and kill the process:
   ps aux | grep uvicorn
   kill <process_id>

   # Start fresh
   cd /home/user/staffingagent/backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify the reset worked**
   - Go to: http://localhost:5173/candidates
   - You should see: "No candidates found"

3. **Upload fresh CVs**
   - Go to: http://localhost:5173/upload
   - Upload some test CVs

---

## Troubleshooting

### "Cannot connect to Docker daemon"
Docker is not running. Start Docker Desktop or Docker service:
```bash
sudo systemctl start docker  # Linux
# Or start Docker Desktop manually on Mac/Windows
```

### "Container not found"
Start docker-compose:
```bash
cd /home/user/staffingagent/docker
docker-compose up -d
```

### "Connection refused"
PostgreSQL container is not running:
```bash
docker ps  # Check if staffing-postgres is in the list
docker start staffing-postgres  # Start it if stopped
```

### "Permission denied"
Run with sudo:
```bash
sudo ./scripts/reset_db_docker.sh --force
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start database | `cd docker && docker-compose up -d postgres` |
| Stop database | `cd docker && docker-compose down` |
| Reset data | `./scripts/reset_db_docker.sh --force` |
| Check status | `docker ps | grep staffing-postgres` |
| View logs | `docker logs staffing-postgres` |
| Connect to DB | `docker exec -it staffing-postgres psql -U postgres -d staffing` |

---

## What Gets Deleted

✅ All candidates
✅ All documents
✅ All CV sections
✅ All embeddings
✅ All availability records
✅ All search history

❌ Database schema (preserved)
❌ Migrations (preserved)
❌ Docker volumes (unless you use nuclear option)
