"""
MAI Framework V2 - MLX-LM HTTP Client
Communicates with bare-metal MLX server via OpenAI-compatible API
"""

import httpx
from typing import AsyncGenerator, Optional, Dict, Any, List
from pydantic import BaseModel
import json

from src.core.utils.config import get_settings
from src.core.utils.logging import get_logger_with_context

logger = get_logger_with_context(module="mlxlm_client")


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str
    messages: List[ChatMessage]
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = False
    stop: Optional[List[str]] = None


class MLXLMClient:
    """
    HTTP client for MLX-LM server.

    Connects to the bare-metal MLX server running on the host machine
    via host.docker.internal when running inside Docker.
    """

    def __init__(self):
        self.settings = get_settings().mlxlm
        self.base_url = self.settings.base_url.rstrip("/")
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=self.settings.timeout,
            write=10.0,
            pool=5.0
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.api_key}"
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if MLX server is healthy.

        Returns:
            Health status including model info
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers()
                )
                response.raise_for_status()

                data = response.json()
                models = data.get("data", [])

                return {
                    "status": "healthy",
                    "connected": True,
                    "models": [m.get("id") for m in models],
                    "current_model": models[0].get("id") if models else None
                }
            except httpx.HTTPError as e:
                logger.error(f"MLX health check failed: {e}")
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": str(e)
                }

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion (non-streaming).

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to config)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            OpenAI-compatible completion response
        """
        payload = {
            "model": model or self.settings.model_name,
            "messages": messages,
            "max_tokens": max_tokens or self.settings.max_tokens,
            "temperature": temperature or self.settings.temperature,
            "stream": False,
            **kwargs
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create a streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to config)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Stream chunks in OpenAI format
        """
        payload = {
            "model": model or self.settings.model_name,
            "messages": messages,
            "max_tokens": max_tokens or self.settings.max_tokens,
            "temperature": temperature or self.settings.temperature,
            "stream": True,
            **kwargs
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            yield chunk
                        except json.JSONDecodeError:
                            continue


# Singleton instance
_mlx_client: Optional[MLXLMClient] = None


def get_mlx_client() -> MLXLMClient:
    """Get or create MLX client singleton."""
    global _mlx_client
    if _mlx_client is None:
        _mlx_client = MLXLMClient()
    return _mlx_client
