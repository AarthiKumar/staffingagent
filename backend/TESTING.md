# Running Tests

## Setup

Make sure you're in the backend directory and have dependencies installed:

```bash
cd backend
pip install -e ".[dev]"  # Install with dev dependencies including pytest
```

## Running All Tests

```bash
# From the backend directory
pytest

# Or with more verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html
```

## Running Specific Tests

```bash
# Run a specific test file
pytest app/tests/unit/test_cv_validation.py

# Run a specific test class
pytest app/tests/unit/test_cv_validation.py::TestSkillValidation

# Run a specific test function
pytest app/tests/unit/test_cv_validation.py::TestSkillValidation::test_valid_skills

# Run tests matching a pattern
pytest -k "validation"
```

## Running Tests on Windows

If you're on Windows and get import errors, run from the backend directory:

```bash
cd C:\Users\aarth\Dropbox\Confidential\Yookthi Labs\Consulting\Staffing Agent\Codebase\staffingagent\backend

# Set PYTHONPATH (Command Prompt)
set PYTHONPATH=%CD%
pytest

# Or (PowerShell)
$env:PYTHONPATH = (Get-Location).Path
pytest

# Or run directly with Python
python -m pytest
```

## Common Test Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest -s` | Show print statements |
| `pytest --lf` | Run only last failed tests |
| `pytest --tb=short` | Shorter tracebacks |
| `pytest -k "skill"` | Run tests matching "skill" |
| `pytest app/tests/unit/` | Run only unit tests |
| `pytest app/tests/integration/` | Run only integration tests |

## Test Structure

```
backend/
├── app/
│   ├── tests/
│   │   ├── conftest.py          # Shared fixtures
│   │   ├── unit/                # Unit tests (no DB/external deps)
│   │   │   ├── test_cv_validation.py
│   │   │   ├── test_normalize.py
│   │   │   ├── test_parser.py
│   │   │   ├── test_ranking.py
│   │   │   └── test_rerank.py
│   │   └── integration/         # Integration tests (with DB)
│   │       └── test_search_flow.py
│   └── ...
├── pytest.ini                   # Pytest configuration
└── pyproject.toml              # Project config with pytest settings
```

## Troubleshooting

### ModuleNotFoundError: No module named 'app'

This means Python can't find the `app` module. Solutions:

1. **Make sure you're in the backend directory:**
   ```bash
   cd backend
   pytest
   ```

2. **Set PYTHONPATH explicitly:**
   ```bash
   # Linux/Mac
   export PYTHONPATH=$PWD
   pytest

   # Windows CMD
   set PYTHONPATH=%CD%
   pytest

   # Windows PowerShell
   $env:PYTHONPATH = (Get-Location).Path
   pytest
   ```

3. **Use Python module syntax:**
   ```bash
   python -m pytest
   ```

4. **Install in editable mode:**
   ```bash
   pip install -e .
   ```

### Tests requiring database

Some integration tests require a PostgreSQL database. You can:

1. **Skip integration tests:**
   ```bash
   pytest app/tests/unit/
   ```

2. **Use Docker database:**
   ```bash
   cd ../docker
   docker-compose up -d postgres
   cd ../backend
   pytest
   ```

3. **Use SQLite for testing:**
   Unit tests use in-memory SQLite by default (no setup needed)

### ImportError for test dependencies

Install dev dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
```

Or install all dev dependencies:
```bash
pip install -e ".[dev]"
```

## CI/CD

Tests should be run in CI/CD pipelines before merging:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd backend
    pytest --cov=app --cov-report=xml
```

## Writing New Tests

1. Place unit tests in `app/tests/unit/`
2. Place integration tests in `app/tests/integration/`
3. Name files `test_*.py`
4. Name test functions `test_*`
5. Use fixtures from `conftest.py`

Example:
```python
def test_my_feature():
    """Test description"""
    # Arrange
    input_data = "test"

    # Act
    result = my_function(input_data)

    # Assert
    assert result == expected_output
```
