# Task: Fix Security Vulnerability and Modularize Routes

**Project**: MAI-v2-Code-Quality (`/Users/maxwell/Projects/mai-v2`)
**Goal**: Replace `request: dict` with Pydantic validation and extract routes into separate modules
**Sequence**: 2 of 6
**Depends On**: 01-create-api-schemas.md

---

## Archon Task Management (REQUIRED)

This task is managed via Archon. Update status as you work.

### Task Info

- **Task ID**: `6b7e3236-2a34-4205-9a15-66fabb1effda`
- **Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`

### Update Status

```bash
# Mark as in_progress when starting
curl -X PUT "http://localhost:8181/api/tasks/6b7e3236-2a34-4205-9a15-66fabb1effda" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done when complete
curl -X PUT "http://localhost:8181/api/tasks/6b7e3236-2a34-4205-9a15-66fabb1effda" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Context

Task 1 created the Pydantic schemas in `src/api/schemas.py`. This task uses those schemas to:

1. **Fix the security vulnerability**: Replace `request: dict` on line 115 of `src/main.py` with `request: ChatCompletionRequest`
2. **Modularize the backend**: Extract inline route definitions into separate route modules

The current `src/main.py` is 151 lines and mixes app initialization, middleware, and all route definitions. After this refactor, routes will be in:
- `src/api/routes/health.py` - Health check endpoints
- `src/api/routes/chat.py` - Chat completion endpoints

---

## Requirements

### 1. Create Routes Directory Structure

```bash
mkdir -p /Users/maxwell/Projects/mai-v2/src/api/routes
touch /Users/maxwell/Projects/mai-v2/src/api/routes/__init__.py
```

### 2. Create Health Routes Module

Create `src/api/routes/health.py`:

```python
"""Health check endpoints."""

from fastapi import APIRouter

from src.core.utils.config import get_settings
from src.infrastructure.llm.mlxlm_client import get_mlx_client

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """Simple health check for Docker."""
    return {"status": "healthy", "version": "2.0.0"}


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check including all services."""
    mlx_client = get_mlx_client()
    mlx_health = await mlx_client.health_check()

    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "services": {
            "mlx": mlx_health,
            "database": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "qdrant": {"status": "healthy"}
        }
    }
```

### 3. Create Chat Routes Module

Create `src/api/routes/chat.py`:

```python
"""Chat completion endpoints."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import ChatCompletionRequest, ChatCompletionResponse
from src.core.utils.logging import get_logger_with_context
from src.infrastructure.llm.mlxlm_client import get_mlx_client

router = APIRouter(prefix="/api/v1", tags=["Chat"])
logger = get_logger_with_context(module="chat")


@router.get("/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "version": "2.0.0",
        "framework": "MAI Framework V2"
    }


@router.get("/agents/llm-status")
async def llm_status():
    """Get LLM connection status."""
    mlx_client = get_mlx_client()
    health = await mlx_client.health_check()

    return {
        "provider": "mlxlm",
        "connected": health["connected"],
        "model": health.get("current_model"),
        "error": health.get("error")
    }


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    Chat completions endpoint with Pydantic validation.
    Proxies to MLX server with OpenAI-compatible format.
    """
    mlx_client = get_mlx_client()

    try:
        response = await mlx_client.chat_completion(
            messages=[msg.model_dump() for msg in request.messages],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return response
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Refactor main.py

Replace `src/main.py` with the refactored version that uses routers:

```python
"""MAI Framework V2 - FastAPI Application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.utils.config import get_settings
from src.core.utils.logging import get_logger_with_context
from src.infrastructure.llm.mlxlm_client import get_mlx_client
from src.api.routes import health, chat

logger = get_logger_with_context(module="main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting MAI Framework V2...")

    # Log configuration (hide sensitive data)
    db_host = settings.database.url.split("@")[-1] if "@" in settings.database.url else "configured"
    logger.info(f"Database: {db_host}")
    logger.info(f"Redis: {settings.redis.url}")
    logger.info(f"MLX Server: {settings.mlxlm.base_url}")

    # Check MLX server connection
    mlx_client = get_mlx_client()
    health_status = await mlx_client.health_check()
    if health_status["connected"]:
        logger.info(f"MLX server connected. Model: {health_status.get('current_model')}")
    else:
        logger.warning(f"MLX server not available: {health_status.get('error')}")
        logger.warning("Chat functionality will be degraded until MLX server is available")

    logger.info("MAI Framework V2 started successfully!")

    yield

    # Cleanup
    logger.info("Shutting down MAI Framework V2...")
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        description="MAI Framework V2 - Mac Studio Hybrid Edition",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(chat.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
```

---

## Files to Create

- `src/api/routes/__init__.py` - Empty package marker
- `src/api/routes/health.py` - Health check endpoints
- `src/api/routes/chat.py` - Chat completion endpoints

## Files to Modify

- `src/main.py` - Refactor to use routers instead of inline routes

---

## Success Criteria

```bash
cd /Users/maxwell/Projects/mai-v2

# Verify routes can be imported
python -c "from src.api.routes import health, chat; print('Routes imported OK')"
# Expected: "Routes imported OK"

# Verify main.py works with routers
python -c "from src.main import app; print(f'App routes: {len(app.routes)}')"
# Expected: Shows route count (should be > 5)

# Verify the security fix - check that request: dict is gone
grep -n "request: dict" src/main.py src/api/routes/*.py
# Expected: No matches (exit code 1)

# Verify ChatCompletionRequest is used
grep -n "ChatCompletionRequest" src/api/routes/chat.py
# Expected: Shows import and usage on endpoint

# Verify validation with curl (if server is running)
# curl -X POST http://localhost:8000/api/v1/chat/completions \
#   -H "Content-Type: application/json" \
#   -d '{"messages": []}'
# Expected: 422 Unprocessable Entity
```

**Checklist:**
- [ ] `src/api/routes/__init__.py` exists
- [ ] `src/api/routes/health.py` exists with health endpoints
- [ ] `src/api/routes/chat.py` exists with chat endpoints
- [ ] `request: dict` is completely removed from codebase
- [ ] `ChatCompletionRequest` is used in chat endpoint
- [ ] `main.py` uses `include_router()` for routes
- [ ] All routes are still accessible at the same paths

---

## Technical Notes

- **Existing routes in main.py**: Lines 68-135 define inline routes
- **Route paths**: Health routes are at root (`/health`), chat routes have `/api/v1` prefix
- **Import pattern**: Use `from src.api.routes import health, chat`
- **Router prefix**: Chat router uses `prefix="/api/v1"` to maintain existing API paths

---

## Important

- Maintain backward compatibility - all existing endpoints must work at the same paths
- The `/health` endpoint must remain at root level (not under `/api/v1`) for Docker healthcheck
- Do NOT change any validation logic - the Pydantic models handle that now
- Ensure proper error responses with HTTPException for 500 errors

---

## On Completion

1. Mark Archon task as `done` using the command above
2. Verify ALL success criteria pass
3. The next task (03-setup-test-infrastructure.md) depends on this completing successfully
