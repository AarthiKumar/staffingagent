# Staffing Agent Backend

FastAPI backend with pgvector semantic search and optional LLM features.

## Architecture

```
app/
  api/v1/          - REST API endpoints
  core/            - Config, logging, security, feature flags
  models/          - SQLAlchemy ORM models
  services/        - Business logic
  db/              - Database session and init
  telemetry/       - Prometheus metrics
  tests/           - Unit and integration tests
```

## Database Schema

- **agents**: Multi-agent configuration
- **documents**: Resume/CV metadata
- **sections**: Document chunks
- **embeddings**: pgvector embeddings with HNSW index
- **candidates**: Candidate profiles
- **availability**: Availability calendar
- **ontology_***: Skills, certs, aliases
- **decisions**: Hiring decisions
- **llm_events**: LLM API call tracking
- **metrics_search**: Search metrics

## Ranking Formula

```python
score = (
    w.cosine * cosine_similarity
    + w.skills * skills_match_ratio
    + w.cert * cert_bonus
    + w.recency * recency_score
)
```

Weights configured per-agent in `config/agents/*.yaml`.

## Embeddings

Default: Local sentence-transformers (`BAAI/bge-small-en`, 384 dim).

To use OpenAI embeddings:
1. Set `EMBEDDINGS_PROVIDER=openai`
2. Implement `_embed_openai()` in `services/embeddings.py`

## LLM Features

### Re-ranking

When `ENABLE_LLM_RERANK=true`:
- Top-K results sent to LLM with structured evidence (no PII, no full CVs)
- 700ms timeout
- Fallback to baseline on error
- Logged to `llm_events` table

### NL→Filters Assistant

When `ENABLE_NL_ASSIST=true`:
- Parse natural language queries into structured filters
- Constrained JSON output
- 600ms timeout
- Fallback to keyword extraction

## Backup Runbook

### Nightly Backup

Add to cron:
```bash
0 2 * * * /path/to/staffing-agent/scripts/backup.sh
```

### Restore Procedure

1. Stop backend: `docker-compose stop backend`
2. Run restore: `./scripts/restore.sh ./backups/staffing_db_YYYYMMDD_HHMMSS.sql.gz`
3. Verify: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM candidates;"`
4. Start backend: `docker-compose start backend`

### Disaster Recovery

If database is corrupted:
1. Restore from most recent backup
2. Re-ingest documents from MinIO originals
3. Validate with eval script: `make eval`

## Performance Tuning

### pgvector Index

HNSW index params (adjust for dataset size):
```sql
CREATE INDEX idx_embeddings_hnsw ON embeddings
USING hnsw (vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Search Optimization

- Pre-filter with SQL before pgvector KNN
- Limit `top_k` to 50 (default)
- Cache embeddings with `input_hash`

### Scaling

- Horizontal: Read replicas for search
- Vertical: Increase Postgres shared_buffers
- Caching: Add Redis for hot queries

## Testing

```bash
pytest                              # All tests
pytest app/tests/unit/              # Unit only
pytest app/tests/integration/       # Integration only
pytest -v -s                        # Verbose
```

## Development

```bash
# Install deps
pip install -e .
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "add new table"

# Start dev server
uvicorn app.main:app --reload
```

## OIDC Implementation Steps

1. Install authlib: `pip install authlib`
2. In `api/v1/auth.py`, implement:
   - `/auth/oidc/login`: Redirect to IdP with OAuth2 flow
   - `/auth/oidc/callback`: Exchange code for token, validate ID token, create session
3. Store OIDC user info in database
4. Update `get_current_user()` to check OIDC session

Example:
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='oidc',
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=f'{settings.oidc_issuer}/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
```

## Troubleshooting

### Embeddings model download fails

If sentence-transformers fails to download model:
```bash
export HF_HOME=/path/to/cache
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en')"
```

### pgvector index not used

Check query plan:
```sql
EXPLAIN ANALYZE SELECT * FROM embeddings ORDER BY vector <=> '[0.1, 0.2, ...]' LIMIT 10;
```

If seq scan, rebuild index:
```sql
REINDEX INDEX idx_embeddings_hnsw;
```

### LLM timeouts

Increase timeout in agent config:
```yaml
llm:
  rerank:
    timeout_ms: 1000
```

## API Documentation

Interactive docs: http://localhost:8000/docs

OpenAPI spec: http://localhost:8000/openapi.json
