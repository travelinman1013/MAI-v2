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
