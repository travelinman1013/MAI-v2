"""
MAI Framework V2 - Intelligence Engine
MLX-LM Server with OpenAI-Compatible API and Hot-Swap Support

This runs OUTSIDE Docker on the bare metal Mac Studio
to leverage the GPU/Neural Engine via unified memory.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import httpx

from config import EngineConfig, get_config


# ============================================
# Models
# ============================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    max_tokens: int = Field(default=2048)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=1.0)
    stream: bool = Field(default=False)
    stop: Optional[List[str]] = None


class LoadModelRequest(BaseModel):
    model: str
    max_tokens: Optional[int] = None


class ServerStatus(BaseModel):
    status: str
    mlx_server_running: bool
    current_model: Optional[str]
    uptime_seconds: float
    port: int


# ============================================
# Engine Manager
# ============================================

class MLXEngineManager:
    """
    Manages the underlying mlx_lm.server process.
    Provides hot-swap capability by stopping and restarting with new models.
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.current_model: Optional[str] = None
        self.start_time: Optional[float] = None
        self._health_check_client = httpx.AsyncClient(timeout=5.0)

    @property
    def mlx_url(self) -> str:
        return f"http://127.0.0.1:{self.config.mlx_internal_port}"

    async def start(self, model: Optional[str] = None) -> bool:
        """Start the MLX-LM server process."""
        if self.process and self.process.poll() is None:
            return True  # Already running

        model = model or self.config.default_model

        cmd = [
            sys.executable, "-m", "mlx_lm.server",
            "--model", model,
            "--host", "127.0.0.1",  # Internal only, we proxy it
            "--port", str(self.config.mlx_internal_port),
            "--max-tokens", str(self.config.max_tokens),
            "--log-level", "INFO"
        ]

        print(f"[Engine] Starting MLX server with model: {model}")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        self.current_model = model
        self.start_time = time.time()

        # Wait for server to be ready
        for _ in range(30):
            if await self._is_healthy():
                print(f"[Engine] MLX server ready on port {self.config.mlx_internal_port}")
                return True
            await asyncio.sleep(1)

        print("[Engine] MLX server failed to start")
        return False

    async def stop(self) -> bool:
        """Stop the MLX-LM server process."""
        if not self.process:
            return True

        print("[Engine] Stopping MLX server...")

        # Graceful shutdown
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

        self.process = None
        self.current_model = None
        self.start_time = None

        print("[Engine] MLX server stopped")
        return True

    async def swap_model(self, new_model: str) -> bool:
        """Hot-swap to a different model."""
        print(f"[Engine] Hot-swapping model: {self.current_model} -> {new_model}")

        await self.stop()
        await asyncio.sleep(2)  # Allow memory to be freed
        return await self.start(new_model)

    async def _is_healthy(self) -> bool:
        """Check if MLX server is responding."""
        try:
            response = await self._health_check_client.get(f"{self.mlx_url}/v1/models")
            return response.status_code == 200
        except:
            return False

    async def proxy_request(
        self,
        method: str,
        path: str,
        body: Optional[Dict] = None,
        stream: bool = False
    ):
        """Proxy request to underlying MLX server."""
        url = f"{self.mlx_url}{path}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            if stream:
                async with client.stream(method, url, json=body) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
            else:
                response = await client.request(method, url, json=body)
                yield response.content

    def get_status(self) -> ServerStatus:
        """Get current server status."""
        running = self.process is not None and self.process.poll() is None
        uptime = time.time() - self.start_time if self.start_time else 0

        return ServerStatus(
            status="running" if running else "stopped",
            mlx_server_running=running,
            current_model=self.current_model,
            uptime_seconds=uptime,
            port=self.config.port
        )


# ============================================
# FastAPI Application
# ============================================

config = get_config()
engine = MLXEngineManager(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print(f"[Engine] MAI Intelligence Engine starting...")
    print(f"[Engine] External port: {config.port}")
    print(f"[Engine] Default model: {config.default_model}")

    # Start MLX server
    success = await engine.start()
    if not success:
        print("[Engine] WARNING: MLX server failed to start")

    yield

    # Cleanup
    print("[Engine] Shutting down...")
    await engine.stop()


app = FastAPI(
    title="MAI Intelligence Engine",
    description="MLX-LM Server with Hot-Swap Support",
    version="2.0.0",
    lifespan=lifespan
)


# ============================================
# Management Endpoints
# ============================================

@app.get("/status")
async def get_status() -> ServerStatus:
    """Get server status."""
    return engine.get_status()


@app.post("/load")
async def load_model(request: LoadModelRequest):
    """Load/swap to a different model."""
    success = await engine.swap_model(request.model)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")

    return {
        "status": "success",
        "model": request.model,
        "message": f"Model {request.model} loaded successfully"
    }


@app.post("/stop")
async def stop_server():
    """Stop the MLX server."""
    await engine.stop()
    return {"status": "stopped"}


@app.post("/start")
async def start_server(model: Optional[str] = None):
    """Start the MLX server."""
    success = await engine.start(model)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start server")
    return {"status": "started", "model": engine.current_model}


@app.get("/models/available")
async def list_available_models():
    """List available models in the model directory."""
    model_dir = Path(config.model_directory)
    if not model_dir.exists():
        return {"models": []}

    models = []
    for path in model_dir.iterdir():
        if path.is_dir() and (path / "config.json").exists():
            models.append({
                "id": path.name,
                "path": str(path)
            })

    return {"models": models}


# ============================================
# OpenAI-Compatible Endpoints (Proxied)
# ============================================

@app.get("/v1/models")
async def list_models():
    """List currently loaded models (OpenAI compatible)."""
    async for response in engine.proxy_request("GET", "/v1/models"):
        return JSONResponse(content=json.loads(response))


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Chat completions endpoint (OpenAI compatible)."""
    body = request.model_dump()

    if request.stream:
        async def stream_generator():
            async for chunk in engine.proxy_request(
                "POST", "/v1/chat/completions", body, stream=True
            ):
                yield chunk

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    else:
        async for response in engine.proxy_request(
            "POST", "/v1/chat/completions", body
        ):
            return JSONResponse(content=json.loads(response))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = engine.get_status()
    return {
        "status": "healthy" if status.mlx_server_running else "degraded",
        "engine": status.model_dump()
    }


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info"
    )
