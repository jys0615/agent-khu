# Testing Guide

How to run the test suite and a log of issues encountered during setup.

---

## Running Tests

```bash
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt pytest httpx

# Run tests
ANTHROPIC_API_KEY=test DATABASE_URL=sqlite:///./test.db \
  pytest tests/test_endpoints.py -v
```

Expected output:
```
tests/test_endpoints.py::test_ready_endpoint PASSED
tests/test_endpoints.py::test_health_endpoint_returns_200 PASSED
tests/test_endpoints.py::test_login_returns_401_for_unknown_user PASSED
tests/test_endpoints.py::test_classifier_simple_query PASSED
tests/test_endpoints.py::test_classifier_complex_query PASSED
tests/test_endpoints.py::test_classifier_length_heuristic PASSED
6 passed in ~1.5s
```

### Why SQLite instead of PostgreSQL

All SQLAlchemy models use standard column types (`String`, `Integer`, `Text`, `Boolean`,
`DateTime`) with no PostgreSQL-specific types (JSONB, ARRAY). SQLite is a drop-in
replacement for testing purposes without requiring a running database server.

### Why no mocking is needed

`app/main.py` wraps every external connection in individual `try/except` blocks inside
the lifespan function. Redis, Elasticsearch, RAG, and the scheduler all fail silently
and log a warning — the app starts up regardless. The HTTP endpoints work normally.

---

## Test Coverage

| Test | Type | Covers |
|------|------|--------|
| `test_ready_endpoint` | HTTP | `GET /ready` returns 200 |
| `test_health_endpoint_returns_200` | HTTP | `GET /health` returns 200 with `status: healthy` |
| `test_login_returns_401_for_unknown_user` | HTTP + DB | Auth logic returns 401 for unknown student ID |
| `test_classifier_simple_query` | Unit | Pattern matching classifies Korean short queries correctly |
| `test_classifier_complex_query` | Unit | Pattern matching classifies recommendation queries correctly |
| `test_classifier_length_heuristic` | Unit | Length > 50 chars defaults to "complex" |

---

## CI/CD

Tests are automatically run via GitHub Actions on every push and pull request to `main`.
See [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

```
CI jobs:
  lint  → ruff check backend/app/
  test  → pytest tests/test_endpoints.py
  build → docker build (context: repo root)
```

---

## Error Log

### 2026-03-28 — Initial test setup

**Error 1: `ModuleNotFoundError: No module named 'app'`**

```
ImportError while importing test module 'tests/test_endpoints.py'
tests/test_endpoints.py:9: in <module>
    from app.question_classifier import QuestionClassifier
E   ModuleNotFoundError: No module named 'app'
```

**Root cause**: pytest's Python path did not include the `backend/` directory,
so `import app.*` failed even when running from inside `backend/`.

**Fix**: Created `backend/pytest.ini` with:
```ini
[pytest]
pythonpath = .
asyncio_mode = auto
asyncio_default_fixture_loop_scope = session
```

`pythonpath = .` tells pytest to add the current directory (`backend/`) to `sys.path`
before collecting tests, making `app` importable.

---

**Error 2: `ModuleNotFoundError: No module named 'passlib'`**

```
app/crud.py:317: ModuleNotFoundError: No module named 'passlib'
```

**Root cause**: `requirements.txt` was not installed in the active Python environment.
`passlib[bcrypt]` is used in `crud.py` for password hashing.

**Fix**: Run `pip install -r requirements.txt` before executing tests.
The CI workflow already does this in the `test` job's "Install dependencies" step,
so this error only surfaces locally when skipping the install step.

---

### 2026-03-28 — CI lint + test failure (GitHub Actions)

**Context**: First push to `main` triggered the CI workflow. Both `lint` and `test` jobs failed.

**Lint — 38 errors across `app/`**

Root cause: pre-existing code quality issues in the source files, surfaced for the first time
by the new `ruff` check. Categories:

| Rule | Count | Files |
|------|-------|-------|
| `F401` unused imports | 11 | `crud.py`, `observability.py`, `routers/` |
| `E402` imports not at top of file | 10 | `crud.py`, `mcp_client.py`, `schemas.py`, `routers/auth.py` |
| `F811` redefinition of unused name | 3 | `schemas.py`, `routers/auth.py` |
| `E712` `== True` comparison | 3 | `crud.py` |
| `F841` unused local variable | 3 | `mcp_client.py`, `question_classifier.py` |
| `F541` f-string without placeholders | 2 | `scheduler.py`, `slm_agent.py` |

Fix strategy:
1. `ruff check --fix` auto-fixed 19 issues (F401, F541, F811 duplicates)
2. Manually fixed remaining 16: moved mid-file imports to top in `crud.py`,
   `mcp_client.py`, `schemas.py`, `routers/auth.py`; replaced `== True` with
   bare boolean; removed unused variable assignments

**Test — exit code 2**

Root cause: `pytest.ini` was created locally but not committed and pushed, so CI
ran without `pythonpath = .`. pytest could not find the `app` module (same as
Error 1 above).

Fix: commit and push `backend/pytest.ini` along with the lint fixes.

---

## Expected Warnings (non-blocking)

These warnings appear in test output but do not affect correctness:

| Warning | Cause | Action needed |
|---------|-------|---------------|
| `PydanticDeprecatedSince20: @validator is deprecated` | `schemas.py` uses Pydantic V1-style `@validator` | Migrate to `@field_validator` in a future refactor |
| `MovedIn20Warning: declarative_base() is deprecated` | `database.py` uses old import path | Update to `sqlalchemy.orm.declarative_base()` |
| `MCP Tool 호출 실패: ValueError: I/O operation on closed file` | MCP subprocess servers are not running in test env | Expected; MCP calls are skipped by the lifespan gracefully |
| `Unclosed client session` | `aiohttp.ClientSession` in Elasticsearch client not closed cleanly | Non-critical in test teardown |
