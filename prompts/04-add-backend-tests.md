# Task: Add Backend Unit Tests

**Project**: MAI-v2-Code-Quality (`/Users/maxwell/Projects/mai-v2`)
**Goal**: Create comprehensive unit tests for schemas, health endpoints, and chat endpoints
**Sequence**: 4 of 6
**Depends On**: 03-setup-test-infrastructure.md

---

## Archon Task Management (REQUIRED)

This task is managed via Archon. Update status as you work.

### Task Info

- **Task ID**: `90b04863-251f-442b-abc4-b6bf9f8fb9d2`
- **Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`

### Update Status

```bash
# Mark as in_progress when starting
curl -X PUT "http://localhost:8181/api/tasks/90b04863-251f-442b-abc4-b6bf9f8fb9d2" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done when complete
curl -X PUT "http://localhost:8181/api/tasks/90b04863-251f-442b-abc4-b6bf9f8fb9d2" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Context

Task 3 set up the pytest infrastructure with fixtures. This task adds the actual unit tests covering:
- **Schema validation** - Test Pydantic models reject invalid data
- **Health endpoints** - Test `/health` and `/health/detailed`
- **Chat endpoints** - Test validation and mocked completions

The tests use the fixtures from `tests/conftest.py` and mock external dependencies (MLX client) to isolate unit behavior.

---

## Requirements

### 1. Create Schema Tests

Create `/Users/maxwell/Projects/mai-v2/tests/test_schemas.py`:

```python
"""Tests for API schemas."""

import pytest
from pydantic import ValidationError

from src.api.schemas import ChatMessage, ChatCompletionRequest


class TestChatMessage:
    def test_valid_user_message(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_valid_assistant_message(self):
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"

    def test_valid_system_message(self):
        msg = ChatMessage(role="system", content="You are helpful.")
        assert msg.role == "system"

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid", content="test")

    def test_empty_content_allowed(self):
        # Empty content is valid in OpenAI API
        msg = ChatMessage(role="user", content="")
        assert msg.content == ""


class TestChatCompletionRequest:
    def test_valid_request_minimal(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")]
        )
        assert len(request.messages) == 1
        assert request.max_tokens == 2048  # default
        assert request.temperature == 0.7  # default
        assert request.stream is False  # default

    def test_valid_request_all_fields(self):
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content="Be helpful"),
                ChatMessage(role="user", content="Hi")
            ],
            model="test-model",
            max_tokens=500,
            temperature=0.5,
            top_p=0.9,
            stream=True,
            stop=["\n"]
        )
        assert len(request.messages) == 2
        assert request.model == "test-model"
        assert request.max_tokens == 500
        assert request.temperature == 0.5
        assert request.stop == ["\n"]

    def test_empty_messages_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatCompletionRequest(messages=[])
        assert "min_length" in str(exc_info.value) or "at least" in str(exc_info.value).lower()

    def test_temperature_lower_bound(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hi")],
            temperature=0.0
        )
        assert request.temperature == 0.0

    def test_temperature_upper_bound(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hi")],
            temperature=2.0
        )
        assert request.temperature == 2.0

    def test_temperature_below_range_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=-0.1
            )

    def test_temperature_above_range_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=2.1
            )

    def test_max_tokens_valid_range(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hi")],
            max_tokens=1
        )
        assert request.max_tokens == 1

    def test_max_tokens_zero_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                max_tokens=0
            )

    def test_max_tokens_negative_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                max_tokens=-1
            )
```

### 2. Create Health Endpoint Tests

Create `/Users/maxwell/Projects/mai-v2/tests/test_health.py`:

```python
"""Tests for health endpoints."""

import pytest


def test_health_check(client):
    """Test basic health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"


def test_detailed_health(client):
    """Test detailed health endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "mlx" in data["services"]


def test_api_status(client):
    """Test API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["version"] == "2.0.0"
    assert data["framework"] == "MAI Framework V2"


def test_llm_status(client):
    """Test LLM status endpoint."""
    response = client.get("/api/v1/agents/llm-status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mlxlm"
    assert "connected" in data
```

### 3. Create Chat Endpoint Tests

Create `/Users/maxwell/Projects/mai-v2/tests/test_chat.py`:

```python
"""Tests for chat endpoints."""

import pytest
from unittest.mock import patch, AsyncMock


def test_chat_completions_validation_empty_messages(client):
    """Test that empty messages are rejected with 422."""
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": []}
    )
    assert response.status_code == 422


def test_chat_completions_validation_invalid_role(client):
    """Test that invalid role is rejected with 422."""
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "invalid", "content": "test"}]}
    )
    assert response.status_code == 422


def test_chat_completions_validation_temperature_too_high(client):
    """Test that out-of-range temperature is rejected."""
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": 5.0
        }
    )
    assert response.status_code == 422


def test_chat_completions_validation_temperature_negative(client):
    """Test that negative temperature is rejected."""
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": -1.0
        }
    )
    assert response.status_code == 422


def test_chat_completions_validation_max_tokens_zero(client):
    """Test that zero max_tokens is rejected."""
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 0
        }
    )
    assert response.status_code == 422


@patch('src.api.routes.chat.get_mlx_client')
def test_chat_completions_success(mock_get_client, client, sample_chat_request):
    """Test successful chat completion with mocked MLX client."""
    mock_client = AsyncMock()
    mock_client.chat_completion.return_value = {
        "id": "test-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "test-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop"
        }]
    }
    mock_get_client.return_value = mock_client

    response = client.post(
        "/api/v1/chat/completions",
        json=sample_chat_request
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-123"
    assert data["choices"][0]["message"]["content"] == "Hello!"


@patch('src.api.routes.chat.get_mlx_client')
def test_chat_completions_mlx_error(mock_get_client, client, sample_chat_request):
    """Test chat completion handles MLX client errors."""
    mock_client = AsyncMock()
    mock_client.chat_completion.side_effect = Exception("MLX server unavailable")
    mock_get_client.return_value = mock_client

    response = client.post(
        "/api/v1/chat/completions",
        json=sample_chat_request
    )
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
```

---

## Files to Create

- `tests/test_schemas.py` - Schema validation tests
- `tests/test_health.py` - Health endpoint tests
- `tests/test_chat.py` - Chat endpoint tests

---

## Success Criteria

```bash
cd /Users/maxwell/Projects/mai-v2

# Run all tests
pytest tests/ -v
# Expected: All tests pass

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing
# Expected: Coverage report showing >70% for src/api/

# Run specific test file
pytest tests/test_schemas.py -v
# Expected: All schema tests pass

# Count tests
pytest tests/ --collect-only | grep "test session starts" -A 100 | grep "<Function" | wc -l
# Expected: At least 20 tests
```

**Checklist:**
- [ ] `tests/test_schemas.py` exists with validation tests
- [ ] `tests/test_health.py` exists with health endpoint tests
- [ ] `tests/test_chat.py` exists with chat endpoint tests
- [ ] All tests pass with `pytest tests/ -v`
- [ ] Empty messages return 422 status
- [ ] Invalid roles return 422 status
- [ ] Out-of-range values return 422 status
- [ ] Mocked success case returns 200 with response data

---

## Technical Notes

- **unittest.mock**: Use `patch` and `AsyncMock` for mocking async MLX client
- **Fixture usage**: Tests use `client` and `sample_chat_request` from conftest.py
- **422 status**: FastAPI returns 422 for Pydantic validation errors
- **500 status**: MLX client errors should return 500 with detail message

---

## Important

- Tests must be isolated - use mocks for external dependencies
- Do NOT make actual calls to MLX server in tests
- Validation tests confirm the security fix from Task 2 is working
- Test both success and failure cases for endpoints

---

## On Completion

1. Mark Archon task as `done` using the command above
2. Verify ALL success criteria pass
3. The next task (05-enhance-frontend.md) depends on this completing successfully
