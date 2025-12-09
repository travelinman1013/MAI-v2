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
