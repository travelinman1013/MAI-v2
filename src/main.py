"""
MAI Framework V2 - FastAPI Application
"""

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
    mlx_health = await mlx_client.health_check()
    if mlx_health["connected"]:
        logger.info(f"MLX server connected. Model: {mlx_health.get('current_model')}")
    else:
        logger.warning(f"MLX server not available: {mlx_health.get('error')}")
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
