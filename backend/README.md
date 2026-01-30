# Staffing Agent Backend

A FastAPI-based staffing agent for CV parsing, candidate search, and availability management.

## Quick Start

### Installation

```bash
cd backend

# Install in editable mode with all dependencies
pip install -e ".[dev]"
```

This installs the package so the `app` module is importable from anywhere, solving all import errors.

### Run Tests

```bash
pytest
```

### Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Installation Options

### Option 1: Editable Install (Recommended for Development) ⭐

```bash
cd backend
pip install -e ".[dev]"
```

**Benefits:**
- ✅ Makes `app` module importable system-wide
- ✅ Code changes take effect immediately (no reinstall needed)
- ✅ Includes dev tools (pytest, black, ruff, mypy)
- ✅ Solves `ModuleNotFoundError: No module named 'app'`

### Option 2: Using requirements.txt

```bash
cd backend
pip install -r requirements.txt
```

**Use this if:** You just want to install dependencies without setting up the package.

### Option 3: Regular Install

```bash
cd backend
pip install .
```

**Note:** Changes require reinstalling. Use `-e` flag for development.

---

## Running Tests

After installation:

```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/unit/test_cv_validation.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run verbose
pytest -v

# Run and stop on first failure
pytest -x
```

See [TESTING.md](TESTING.md) for comprehensive testing guide.

---

## Configuration

Create `.env` file in backend directory:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/staffing
EMBEDDINGS_MODEL=BAAI/bge-small-en
EMBEDDINGS_PROVIDER=local
LLM_PROVIDER=disabled
```

---

## Development Workflow

1. **Install in editable mode:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Make changes** - No reinstall needed!

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Format code:**
   ```bash
   black app/
   ```

5. **Lint:**
   ```bash
   ruff check app/
   ```

6. **Type check:**
   ```bash
   mypy app/
   ```

---

## Project Structure

```
backend/
├── app/                      # Main application package
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── api/                 # API endpoints
│   │   └── v1/
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   │   ├── parsing/         # CV parsing
│   │   ├── cv_validation.py # Data validation
│   │   └── ...
│   └── tests/               # Tests
│       ├── conftest.py
│       ├── unit/
│       └── integration/
├── alembic/                 # Database migrations
├── config/                  # Config files (ontology)
├── scripts/                 # Utility scripts
├── pyproject.toml          # Package config
├── requirements.txt        # Dependencies
├── pytest.ini              # Pytest config
└── README.md               # This file
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
cd backend
pip install -e .
```

This makes the `app` module importable system-wide.

### Tests fail with import errors

**Solution:**
```bash
pip install -e ".[dev]"  # Install with dev dependencies
```

### Changes not reflected after editing code

If you used `pip install .` (without `-e`), changes require reinstalling.

**Solution:** Use editable mode instead:
```bash
pip install -e .
```

### Database connection errors

Make sure Docker services are running:
```bash
cd ../docker
docker-compose up -d postgres
```

Or check your `.env` file has the correct `DATABASE_URL`.

---

## Documentation

- [Testing Guide](TESTING.md) - How to run and write tests
- [Database Reset](../RESET_DATABASE_INSTRUCTIONS.md) - How to reset database
- [API Docs](http://localhost:8000/docs) - Auto-generated (when server runs)

---

## Key Features

- ✅ **CV Parsing** - Extracts skills, experience, certifications from PDF/Word
- ✅ **Data Validation** - Filters passport numbers, IDs, personal data
- ✅ **Ontology Normalization** - Maps aliases to canonical skills
- ✅ **Semantic Search** - Vector embeddings with pgvector
- ✅ **Duplicate Detection** - Identifies and merges duplicate candidates
- ✅ **Section Editing** - Edit CV sections with auto-embedding regeneration
