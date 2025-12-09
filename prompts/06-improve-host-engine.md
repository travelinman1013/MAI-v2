# Task: Improve Host Engine Process Management

**Project**: MAI-v2-Code-Quality (`/Users/maxwell/Projects/mai-v2`)
**Goal**: Add signal handling, crash recovery with exponential backoff, and process monitoring
**Sequence**: 6 of 6
**Depends On**: 05-enhance-frontend.md

---

## Archon Task Management (REQUIRED)

This task is managed via Archon. Update status as you work.

### Task Info

- **Task ID**: `024ae69f-effc-46df-9a9f-ceb7d2b36539`
- **Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`

### Update Status

```bash
# Mark as in_progress when starting
curl -X PUT "http://localhost:8181/api/tasks/024ae69f-effc-46df-9a9f-ceb7d2b36539" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done when complete
curl -X PUT "http://localhost:8181/api/tasks/024ae69f-effc-46df-9a9f-ceb7d2b36539" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Context

Tasks 1-5 addressed the backend and frontend. This final task improves the host engine's process management.

The current `host_engine/server.py` has basic subprocess handling in the `MLXEngineManager` class (lines 64-187). The improvements add:
1. **Signal handling**: Proper process group management for clean shutdown
2. **Crash recovery**: Exponential backoff retry when the MLX process dies
3. **Background monitoring**: Detect crashes and auto-recover

This makes the host engine more resilient for production use.

---

## Requirements

### 1. Update MLXEngineManager Class

Update the `MLXEngineManager` class in `/Users/maxwell/Projects/mai-v2/host_engine/server.py`:

```python
import signal
import os

class MLXEngineManager:
    """
    Manages the underlying mlx_lm.server process.
    Provides hot-swap capability and crash recovery.
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.current_model: Optional[str] = None
        self.start_time: Optional[float] = None
        self._health_check_client = httpx.AsyncClient(timeout=5.0)
        self._restart_attempts = 0
        self._max_restart_attempts = 3
        self._monitoring = False

    @property
    def mlx_url(self) -> str:
        return f"http://127.0.0.1:{self.config.mlx_internal_port}"

    async def start(self, model: Optional[str] = None) -> bool:
        """Start the MLX-LM server process with crash recovery."""
        if self.process and self.process.poll() is None:
            return True  # Already running

        model = model or self.config.default_model

        cmd = [
            sys.executable, "-m", "mlx_lm.server",
            "--model", model,
            "--host", "127.0.0.1",
            "--port", str(self.config.mlx_internal_port),
            "--max-tokens", str(self.config.max_tokens),
            "--log-level", "INFO"
        ]

        print(f"[Engine] Starting MLX server with model: {model}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )
        except Exception as e:
            print(f"[Engine] Failed to start process: {e}")
            return False

        self.current_model = model
        self.start_time = time.time()

        # Wait for server to be ready
        for i in range(30):
            if self.process.poll() is not None:
                # Process died during startup
                print(f"[Engine] Process died during startup (exit code: {self.process.returncode})")
                return await self._handle_crash()

            if await self._is_healthy():
                print(f"[Engine] MLX server ready on port {self.config.mlx_internal_port}")
                self._restart_attempts = 0  # Reset on success
                return True

            await asyncio.sleep(1)

        print("[Engine] MLX server failed to become healthy")
        return False

    async def _handle_crash(self) -> bool:
        """Handle process crash with exponential backoff retry."""
        self._restart_attempts += 1

        if self._restart_attempts > self._max_restart_attempts:
            print(f"[Engine] Max restart attempts ({self._max_restart_attempts}) exceeded")
            self._restart_attempts = 0  # Reset for future manual starts
            return False

        backoff = 2 ** self._restart_attempts
        print(f"[Engine] Restart attempt {self._restart_attempts}/{self._max_restart_attempts} in {backoff}s")
        await asyncio.sleep(backoff)

        # Clean up dead process
        self.process = None
        return await self.start(self.current_model)

    async def stop(self) -> bool:
        """Stop the MLX-LM server process gracefully."""
        if not self.process:
            return True

        print("[Engine] Stopping MLX server...")
        self._monitoring = False

        try:
            # Send SIGTERM to process group for clean shutdown
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("[Engine] Graceful shutdown timed out, force killing...")
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait(timeout=5)
        except ProcessLookupError:
            pass  # Process already dead
        except Exception as e:
            print(f"[Engine] Error during shutdown: {e}")

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

    async def start_monitoring(self):
        """Start background monitoring for crash recovery."""
        if self._monitoring:
            return

        self._monitoring = True
        print("[Engine] Starting process monitor")

        while self._monitoring:
            await asyncio.sleep(10)

            if not self._monitoring:
                break

            if self.process and self.process.poll() is not None:
                print(f"[Engine] Process died unexpectedly (exit code: {self.process.returncode})")
                self.process = None
                await self._handle_crash()

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False

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
```

### 2. Update Lifespan to Start Monitoring

Update the lifespan function in `host_engine/server.py`:

```python
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
    else:
        # Start background monitoring
        asyncio.create_task(engine.start_monitoring())

    yield

    # Cleanup
    print("[Engine] Shutting down...")
    engine.stop_monitoring()
    await engine.stop()
```

### 3. Add Restart Attempts to Status

Update the `ServerStatus` model and `get_status` method:

```python
class ServerStatus(BaseModel):
    status: str
    mlx_server_running: bool
    current_model: Optional[str]
    uptime_seconds: float
    port: int
    restart_attempts: int = 0  # Add this field

def get_status(self) -> ServerStatus:
    """Get current server status."""
    running = self.process is not None and self.process.poll() is None
    uptime = time.time() - self.start_time if self.start_time else 0

    return ServerStatus(
        status="running" if running else "stopped",
        mlx_server_running=running,
        current_model=self.current_model,
        uptime_seconds=uptime,
        port=self.config.port,
        restart_attempts=self._restart_attempts
    )
```

---

## Files to Modify

- `host_engine/server.py` - Update MLXEngineManager with improved process management

---

## Success Criteria

```bash
cd /Users/maxwell/Projects/mai-v2

# Verify signal import is present
grep "import signal" host_engine/server.py
# Expected: Shows import line

# Verify os.setsid is used for process group
grep "preexec_fn=os.setsid" host_engine/server.py
# Expected: Shows the line

# Verify crash recovery method exists
grep "_handle_crash" host_engine/server.py
# Expected: Shows async def _handle_crash

# Verify monitoring methods exist
grep "start_monitoring\|stop_monitoring" host_engine/server.py
# Expected: Shows both methods

# Verify exponential backoff
grep "2 \*\* self._restart_attempts" host_engine/server.py
# Expected: Shows backoff calculation

# Syntax check
python -m py_compile host_engine/server.py
# Expected: No errors
```

**Checklist:**
- [ ] `import signal` and `import os` are present
- [ ] `preexec_fn=os.setsid` used in Popen for process group
- [ ] `_handle_crash()` method implements exponential backoff
- [ ] `_max_restart_attempts = 3` limit is set
- [ ] `start_monitoring()` runs background task
- [ ] `stop_monitoring()` cleanly stops the task
- [ ] `stop()` uses `os.killpg()` for clean shutdown
- [ ] `ServerStatus` includes `restart_attempts`
- [ ] Code compiles without syntax errors

---

## Technical Notes

- **Process groups**: `os.setsid` creates new session, `os.killpg` kills the group
- **Exponential backoff**: 2s, 4s, 8s delays between restart attempts
- **asyncio.create_task**: Runs monitoring in background without blocking
- **ProcessLookupError**: Caught when process already dead during kill

---

## Important

- Do NOT change the API endpoints - only the internal process management
- The monitoring loop must be cancellable (check `_monitoring` flag)
- Ensure proper cleanup in all error paths
- The max restart attempts should prevent infinite crash loops

---

## On Completion

1. Mark Archon task as `done` using the command above
2. Verify ALL success criteria pass
3. This is the final task - create completion document below

### Create Completion Document

```bash
curl -X POST "http://localhost:8181/api/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "MAI-v2-Code-Quality - Implementation Complete",
    "content": "# MAI-v2-Code-Quality Ready\n\nAll 6 implementation tasks complete:\n1. Created API Schemas with Pydantic validation\n2. Fixed security vulnerability and modularized routes\n3. Set up pytest infrastructure\n4. Added backend unit tests\n5. Enhanced frontend with ModelStatus component\n6. Improved host engine process management\n\n## Verification\n- Run tests: `pytest tests/ -v`\n- Check coverage: `pytest tests/ --cov=src`\n- Start server: `uvicorn src.main:app`\n- Validate endpoints at `/api/docs`",
    "project_id": "63fd8b5b-fde0-4034-bbd3-2a671551a348"
  }'
```
