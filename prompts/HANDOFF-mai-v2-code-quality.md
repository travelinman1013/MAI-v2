# MAI-v2-Code-Quality - Sequential Implementation Handoff

## Project Overview

**Project**: MAI-v2-Code-Quality
**Archon Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`
**Working Directory**: `/Users/maxwell/Projects/mai-v2`
**Goal**: Fix security vulnerabilities, refactor backend, add tests, enhance frontend, improve process management

---

## Problem Summary

A comprehensive code review identified several issues in the MAI Framework V2 project:

1. **CRITICAL Security Vulnerability**: The `/api/v1/chat/completions` endpoint accepts `request: dict` instead of a Pydantic model, bypassing FastAPI's automatic validation
2. **Zero Test Coverage**: No test files exist in the project
3. **Monolithic Backend**: `src/main.py` mixes app initialization, middleware, and all route definitions
4. **Basic Frontend**: Missing model status indicator component
5. **Basic Process Management**: Host engine subprocess handling lacks robust error recovery

---

## Prompts to Execute

Execute these prompts **sequentially** in order. Each depends on the previous:

| # | File | Description | Archon Task ID |
|---|------|-------------|----------------|
| 1 | `01-create-api-schemas.md` | Create Pydantic request/response models | `1c3043af-720f-40e6-9539-7657d0a8bc2e` |
| 2 | `02-fix-security-modularize.md` | Fix security vulnerability, extract routes | `6b7e3236-2a34-4205-9a15-66fabb1effda` |
| 3 | `03-setup-test-infrastructure.md` | Add pytest, create test fixtures | `f96c8220-c09d-460d-aa64-ce0284295ebc` |
| 4 | `04-add-backend-tests.md` | Write unit tests for schemas and endpoints | `90b04863-251f-442b-abc4-b6bf9f8fb9d2` |
| 5 | `05-enhance-frontend.md` | Add ModelStatus component | `9667a68c-de3e-4565-8e79-23366e3f1fb8` |
| 6 | `06-improve-host-engine.md` | Add process recovery and monitoring | `024ae69f-effc-46df-9a9f-ceb7d2b36539` |

---

## Execution Instructions

### Option 1: Use Sequential Workflow Skill

```
I want to execute the sequential prompts in /Users/maxwell/Projects/mai-v2/prompts/
Starting from prompt 01.
```

### Option 2: Manual Execution

For each prompt file:

1. Read the prompt file
2. Mark Archon task as `in_progress`
3. Execute all requirements in the prompt
4. Verify success criteria pass
5. Mark Archon task as `done`
6. Proceed to next prompt

---

## Files Created/Modified Summary

### Created
- `src/api/__init__.py`
- `src/api/schemas.py`
- `src/api/routes/__init__.py`
- `src/api/routes/health.py`
- `src/api/routes/chat.py`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_schemas.py`
- `tests/test_health.py`
- `tests/test_chat.py`
- `pytest.ini`
- `frontend/src/components/ModelStatus.tsx`

### Modified
- `src/main.py` - Refactored to use routers
- `requirements.txt` - Added test dependencies
- `host_engine/server.py` - Added process recovery
- `frontend/src/App.tsx` - Added ModelStatus component
- `frontend/src/index.css` - Added status indicator styles

---

## Success Criteria

After all prompts are executed:

- [ ] `request: dict` is completely removed from codebase
- [ ] Invalid API requests return 422 with validation errors
- [ ] `pytest tests/ -v` passes all tests
- [ ] Test coverage > 70% for `src/api/`
- [ ] Frontend shows model status indicator in header
- [ ] Host engine auto-recovers from process crashes

---

## Verification Commands

```bash
cd /Users/maxwell/Projects/mai-v2

# Check security fix
grep -r "request: dict" src/
# Expected: No matches

# Run tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Verify imports
python -c "from src.api.routes import health, chat; print('OK')"

# Frontend build
cd frontend && npm run build
```

---

## Tech Stack Reference

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, httpx
- **Frontend**: React 18, TypeScript, Vite
- **Host Engine**: Python, MLX-LM, uvicorn
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Archon**: http://localhost:8181
