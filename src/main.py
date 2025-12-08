"""
MAI Framework V2 - FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.utils.config import get_settings
from src.core.utils.logging import get_logger_with_context
from src.infrastructure.llm.mlxlm_client import get_mlx_client

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
    health = await mlx_client.health_check()
    if health["connected"]:
        logger.info(f"MLX server connected. Model: {health.get('current_model')}")
    else:
        logger.warning(f"MLX server not available: {health.get('error')}")
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

    # Health check at root level (for Docker healthcheck)
    @app.get("/health")
    async def health_check():
        """Simple health check for Docker."""
        return {"status": "healthy", "version": "2.0.0"}

    @app.get("/health/detailed")
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
                "database": {"status": "healthy"},  # TODO: Add actual DB check
                "redis": {"status": "healthy"},     # TODO: Add actual Redis check
                "qdrant": {"status": "healthy"}     # TODO: Add actual Qdrant check
            }
        }

    # API routes placeholder (to be expanded)
    @app.get("/api/v1/status")
    async def api_status():
        """API status endpoint."""
        return {
            "status": "operational",
            "version": "2.0.0",
            "framework": "MAI Framework V2"
        }

    @app.get("/api/v1/agents/llm-status")
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

    @app.post("/api/v1/chat/completions")
    async def chat_completions(request: dict):
        """
        Chat completions endpoint.
        Proxies to MLX server with OpenAI-compatible format.
        """
        mlx_client = get_mlx_client()

        messages = request.get("messages", [])
        if not messages:
            return {"error": "No messages provided"}

        try:
            response = await mlx_client.chat_completion(
                messages=messages,
                max_tokens=request.get("max_tokens"),
                temperature=request.get("temperature")
            )
            return response
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return {"error": str(e)}

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
