# Staffing Agent MVP

Production-ready internal staffing agent with optional LLM features.

## Features

- **Semantic Search**: pgvector-powered candidate search with configurable ranking
- **Multi-Agent Platform**: Pluggable parsers, embeddings providers, and per-agent configuration
- **Optional LLM Features**: Re-ranking and NL→filters assistant (disabled by default)
- **Observability**: Prometheus metrics, structured logs, cost tracking
- **Portable**: Runs locally via Docker Compose or bare metal

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16+ with pgvector

### Setup

1. **Clone and configure**:
   ```bash
   cd staffingagent
   cp backend/.env.example backend/.env
   # Edit backend/.env with your settings
   ```

2. **Start infrastructure**:
   ```bash
   make db
   ```

3. **Run migrations**:
   ```bash
   make migrate
   ```

4. **Start backend** (Terminal 1):
   ```bash
   make dev-backend
   ```

5. **Start frontend** (Terminal 2):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Seed sample data**:
   ```bash
   make seed
   ```

7. **Open browser**: http://localhost:5173

## API Endpoints

### Search
```bash
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "staffing",
    "filters": {
      "required_skills": ["kubernetes", "python"],
      "required_certs": ["aws devops professional"]
    },
    "text": "Need senior DevOps engineer",
    "use_llm_rerank": false
  }'
```

### Ingest Resume
```bash
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "staffing",
    "document_type": "resume",
    "filename": "resume.pdf",
    "content_base64": "..."
  }'
```

### Health Check
```bash
curl http://localhost:8000/api/v1/healthz
```

### Metrics
```bash
curl http://localhost:8000/api/v1/metrics
```

## Configuration

### Agent Config (`config/agents/staffing.yaml`)

```yaml
agent_id: staffing
ranking:
  weights:
    cosine: 0.55
    skills: 0.25
    cert: 0.10
    recency: 0.10
llm:
  rerank:
    enabled: false
    timeout_ms: 700
  nl_assist:
    enabled: false
budgets:
  monthly_usd: 150.0
```

### Environment Variables

See `backend/.env.example` for all options.

**Key settings**:
- `EMBEDDINGS_MODEL`: Sentence-transformers model (default: `BAAI/bge-small-en`)
- `LLM_PROVIDER`: `disabled` | `openai` | `anthropic` | `vertexai`
- `ENABLE_LLM_RERANK`: `false` (default)
- `ENABLE_NL_ASSIST`: `false` (default)

## Testing

```bash
make test           # Run unit + integration tests
make eval           # Run relevance evaluation
```

## Evaluation

Baseline search should achieve **P@5 ≥ 0.60**. LLM re-rank must add **≥ +0.10** absolute P@5 to be enabled by default.

```bash
make eval
# View results in metrics.json
```

## Deployment

### Docker Compose (Full Stack)

```bash
cd docker
docker-compose up -d
```

Services:
- Postgres: localhost:5432
- MinIO: localhost:9000 (console: :9001)
- Prometheus: localhost:9090
- Grafana: localhost:3000 (admin/admin)

### Bare Metal

1. Install dependencies:
   ```bash
   cd backend
   pip install -e .
   ```

2. Run backend:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. Build frontend:
   ```bash
   cd frontend
   npm run build
   # Serve dist/ with your preferred web server
   ```

## Backup & Restore

### Backup

```bash
./scripts/backup.sh
```

Backups saved to `./backups/` (keeps last 30 days).

### Restore

```bash
./scripts/restore.sh ./backups/staffing_db_20250101_120000.sql.gz
```

See `backend/README.md` for detailed runbook.

## OIDC Authentication

By default, local auth is enabled with user `admin:admin`.

To enable OIDC:

1. Set in `.env`:
   ```
   OIDC_ENABLED=true
   OIDC_ISSUER=https://your-idp.com
   OIDC_CLIENT_ID=your-client-id
   OIDC_CLIENT_SECRET=your-secret
   ```

2. Implement OIDC flow in `backend/app/api/v1/auth.py` (see TODOs)

## Swapping Providers

### Embeddings

Edit `.env`:
```
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDINGS_PROVIDER=local
```

Or implement custom provider in `backend/app/services/embeddings.py`.

### LLM

Edit `.env`:
```
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
ENABLE_LLM_RERANK=true
ENABLE_NL_ASSIST=true
```

Implement provider logic in `backend/app/services/rerank.py` and `nl_filters.py`.

## Observability

- **Logs**: JSON structured logs to stdout
- **Metrics**: Prometheus at `:9001/metrics`
- **Grafana**: Pre-configured dashboards (optional)

Key metrics:
- `staffing_requests_total`
- `staffing_search_results`
- `staffing_llm_tokens_in_total`
- `staffing_llm_cost_usd_total`
- `staffing_current_month_spend_usd`

## Cost Management

Per-agent budgets are enforced. When exceeded, LLM features auto-disable.

View current spend:
```bash
curl http://localhost:8000/api/v1/costs/budget
```

## License

MIT

## Support

For issues or questions: https://github.com/your-org/staffing-agent/issues
