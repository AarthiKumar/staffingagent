.PHONY: help dev db seed test eval clean

help:
	@echo "Staffing Agent Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make dev       - Start backend and frontend in dev mode"
	@echo "  make db        - Start Postgres + MinIO via Docker Compose"
	@echo "  make migrate   - Run database migrations"
	@echo "  make seed      - Seed sample candidate data"
	@echo "  make test      - Run backend tests"
	@echo "  make eval      - Run relevance evaluation"
	@echo "  make clean     - Stop all services and clean data"

db:
	cd docker && docker-compose up -d postgres minio
	@echo "Waiting for database to be ready..."
	@sleep 5

migrate: db
	cd backend && alembic upgrade head

seed:
	python3 scripts/seed_sample_data.py

test:
	cd backend && pytest

eval:
	python3 scripts/eval_relevance.py

dev-backend: migrate
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Run these in separate terminals:"
	@echo "  Terminal 1: make db"
	@echo "  Terminal 2: make dev-backend"
	@echo "  Terminal 3: make dev-frontend"

clean:
	cd docker && docker-compose down -v
	rm -rf backend/data
	rm -f metrics.json
