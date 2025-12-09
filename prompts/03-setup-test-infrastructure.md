# Task: Setup Test Infrastructure

**Project**: MAI-v2-Code-Quality (`/Users/maxwell/Projects/mai-v2`)
**Goal**: Add pytest dependencies, create test directory structure, and configure test fixtures
**Sequence**: 3 of 6
**Depends On**: 02-fix-security-modularize.md

---

## Archon Task Management (REQUIRED)

This task is managed via Archon. Update status as you work.

### Task Info

- **Task ID**: `f96c8220-c09d-460d-aa64-ce0284295ebc`
- **Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`

### Update Status

```bash
# Mark as in_progress when starting
curl -X PUT "http://localhost:8181/api/tasks/f96c8220-c09d-460d-aa64-ce0284295ebc" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done when complete
curl -X PUT "http://localhost:8181/api/tasks/f96c8220-c09d-460d-aa64-ce0284295ebc" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Context

Tasks 1-2 created the API schemas and modularized routes. The project currently has **zero test coverage**. This task sets up the pytest infrastructure that Task 4 will use to add actual tests.

The testing setup includes:
- pytest with async support
- Test client fixtures for FastAPI
- Sample request fixtures for reuse across tests

---

## Requirements

### 1. Add Test Dependencies to requirements.txt

Append the following to `/Users/maxwell/Projects/mai-v2/requirements.txt`:

```
# Testing
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-cov>=4.1.0
```

Note: `httpx` is already in requirements.txt (line 8) and is used for async test client.

### 2. Create pytest Configuration

Create `/Users/maxwell/Projects/mai-v2/pytest.ini`:

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

### 3. Create Test Directory Structure

```bash
mkdir -p /Users/maxwell/Projects/mai-v2/tests
touch /Users/maxwell/Projects/mai-v2/tests/__init__.py
```

### 4. Create Test Fixtures

Create `/Users/maxwell/Projects/mai-v2/tests/conftest.py`:

```python
"""Shared test fixtures for MAI Framework V2."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
def client():
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for async endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_chat_request():
    """Sample valid chat request."""
    return {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }


@pytest.fixture
def invalid_empty_messages():
    """Invalid request with empty messages."""
    return {
        "messages": []
    }


@pytest.fixture
def invalid_role_request():
    """Invalid request with bad role."""
    return {
        "messages": [{"role": "invalid", "content": "test"}]
    }


@pytest.fixture
def invalid_temperature_request():
    """Invalid request with out-of-range temperature."""
    return {
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 5.0
    }
```

---

## Files to Create

- `tests/__init__.py` - Empty package marker
- `tests/conftest.py` - Shared test fixtures
- `pytest.ini` - pytest configuration

## Files to Modify

- `requirements.txt` - Add testing dependencies

---

## Success Criteria

```bash
cd /Users/maxwell/Projects/mai-v2

# Verify test dependencies are in requirements.txt
grep "pytest" requirements.txt
# Expected: Shows pytest>=8.0.0, pytest-asyncio>=0.24.0, pytest-cov>=4.1.0

# Verify pytest.ini exists and has correct content
cat pytest.ini
# Expected: Shows testpaths = tests, asyncio_mode = auto

# Verify tests directory exists
ls -la tests/
# Expected: Shows __init__.py and conftest.py

# Verify fixtures can be loaded
python -c "
import sys
sys.path.insert(0, '.')
from tests.conftest import sample_chat_request, client
print('Fixtures can be imported OK')
"
# Expected: "Fixtures can be imported OK"

# Install test dependencies and verify pytest works
pip install pytest pytest-asyncio pytest-cov
pytest --collect-only tests/
# Expected: Shows test collection (may be empty if no test files yet)
```

**Checklist:**
- [ ] `pytest>=8.0.0` added to requirements.txt
- [ ] `pytest-asyncio>=0.24.0` added to requirements.txt
- [ ] `pytest-cov>=4.1.0` added to requirements.txt
- [ ] `pytest.ini` exists with correct configuration
- [ ] `tests/__init__.py` exists
- [ ] `tests/conftest.py` exists with fixtures
- [ ] `client` fixture creates TestClient
- [ ] `async_client` fixture creates AsyncClient
- [ ] Sample request fixtures are defined

---

## Technical Notes

- **pytest-asyncio**: Required for testing async FastAPI endpoints
- **pytest-cov**: Enables coverage reporting with `--cov` flag
- **asyncio_mode = auto**: Automatically handles async test functions
- **ASGITransport**: Used for httpx AsyncClient with FastAPI ASGI apps
- **TestClient**: Synchronous client for simpler tests

---

## Important

- Do NOT add any actual test files yet - that's Task 4
- Ensure pytest.ini is in the project root (not in tests/)
- The fixtures should work with the refactored routes from Task 2
- Keep fixtures simple and focused on reusable data

---

## On Completion

1. Mark Archon task as `done` using the command above
2. Verify ALL success criteria pass
3. The next task (04-add-backend-tests.md) depends on this completing successfully
