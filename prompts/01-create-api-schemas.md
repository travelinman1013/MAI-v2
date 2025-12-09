# Task: Create API Schemas with Pydantic Models

**Project**: MAI-v2-Code-Quality (`/Users/maxwell/Projects/mai-v2`)
**Goal**: Add Pydantic request/response models for OpenAI-compatible chat completions API
**Sequence**: 1 of 6
**Depends On**: None (first step)

---

## Archon Task Management (REQUIRED)

This task is managed via Archon. Update status as you work.

### Task Info

- **Task ID**: `1c3043af-720f-40e6-9539-7657d0a8bc2e`
- **Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`

### Update Status

```bash
# Mark as in_progress when starting
curl -X PUT "http://localhost:8181/api/tasks/1c3043af-720f-40e6-9539-7657d0a8bc2e" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done when complete
curl -X PUT "http://localhost:8181/api/tasks/1c3043af-720f-40e6-9539-7657d0a8bc2e" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Context

The MAI Framework V2 backend has a **CRITICAL security vulnerability**: the `/api/v1/chat/completions` endpoint accepts `request: dict` instead of a Pydantic model. This bypasses FastAPI's automatic validation, allowing malformed data to enter the application.

This task creates a dedicated `src/api/schemas.py` module with properly validated Pydantic models that will be used by the chat endpoint. These models follow the OpenAI chat completions API specification.

The codebase already has similar models in `src/infrastructure/llm/mlxlm_client.py` (lines 17-31) that can serve as reference, but the API layer needs its own comprehensive schema definitions with proper validation constraints.

---

## Requirements

### 1. Create API Directory Structure

Create the `src/api/` package if it doesn't exist:

```bash
mkdir -p /Users/maxwell/Projects/mai-v2/src/api
touch /Users/maxwell/Projects/mai-v2/src/api/__init__.py
```

### 2. Create Schemas Module

Create `src/api/schemas.py` with the following Pydantic models:

```python
"""
MAI Framework V2 - API Request/Response Schemas
OpenAI-compatible chat completion models with full validation.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    messages: List[ChatMessage] = Field(..., min_length=1)
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=32768)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False
    stop: Optional[List[str]] = None


class ChatCompletionChoice(BaseModel):
    """Single completion choice."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatCompletionUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None


class ErrorResponse(BaseModel):
    """API error response."""
    error: str
    detail: Optional[str] = None
```

### 3. Key Validation Features

- `ChatMessage.role`: Uses `Literal` type to restrict to valid roles only
- `ChatCompletionRequest.messages`: Must have at least 1 message (`min_length=1`)
- `ChatCompletionRequest.max_tokens`: Range 1-32768
- `ChatCompletionRequest.temperature`: Range 0.0-2.0
- `ChatCompletionRequest.top_p`: Range 0.0-1.0

---

## Files to Create

- `src/api/__init__.py` - Empty package marker
- `src/api/schemas.py` - Pydantic models for API requests/responses

---

## Success Criteria

```bash
# Verify directory structure
ls -la /Users/maxwell/Projects/mai-v2/src/api/
# Expected: __init__.py and schemas.py exist

# Verify models can be imported
cd /Users/maxwell/Projects/mai-v2
python -c "from src.api.schemas import ChatCompletionRequest, ChatCompletionResponse; print('Import OK')"
# Expected: "Import OK"

# Verify validation works
python -c "
from src.api.schemas import ChatCompletionRequest, ChatMessage
from pydantic import ValidationError

# Valid request should work
req = ChatCompletionRequest(messages=[ChatMessage(role='user', content='Hello')])
print(f'Valid request: {len(req.messages)} message(s)')

# Empty messages should fail
try:
    ChatCompletionRequest(messages=[])
except ValidationError as e:
    print('Empty messages rejected: OK')

# Invalid role should fail
try:
    ChatMessage(role='invalid', content='test')
except ValidationError as e:
    print('Invalid role rejected: OK')

# Out of range temperature should fail
try:
    ChatCompletionRequest(
        messages=[ChatMessage(role='user', content='Hi')],
        temperature=5.0
    )
except ValidationError as e:
    print('Invalid temperature rejected: OK')
"
# Expected: All validation tests pass
```

**Checklist:**
- [ ] `src/api/__init__.py` exists
- [ ] `src/api/schemas.py` exists with all models
- [ ] Models can be imported without errors
- [ ] Empty messages list is rejected
- [ ] Invalid role values are rejected
- [ ] Out-of-range temperature/max_tokens are rejected

---

## Technical Notes

- **Reference file**: `src/infrastructure/llm/mlxlm_client.py` has similar models (lines 17-31)
- **Pydantic version**: Project uses Pydantic v2 (see requirements.txt line 11)
- **Field constraints**: Use `Field()` with `ge`, `le`, `min_length` for validation
- **Literal type**: Import from `typing` for strict role validation

---

## Important

- Do NOT modify any existing files in this task
- These schemas will be used by the route modules created in Task 2
- The validation constraints are critical for security - do not weaken them
- Ensure all models can serialize/deserialize properly for API responses

---

## On Completion

1. Mark Archon task as `done` using the command above
2. Verify ALL success criteria pass
3. The next task (02-fix-security-modularize.md) depends on this completing successfully
