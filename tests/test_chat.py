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
