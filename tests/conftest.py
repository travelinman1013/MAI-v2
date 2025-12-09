"""Shared test fixtures for MAI Framework V2."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
def client():
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for async endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_chat_request():
    """Sample valid chat request."""
    return {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }


@pytest.fixture
def invalid_empty_messages():
    """Invalid request with empty messages."""
    return {
        "messages": []
    }


@pytest.fixture
def invalid_role_request():
    """Invalid request with bad role."""
    return {
        "messages": [{"role": "invalid", "content": "test"}]
    }


@pytest.fixture
def invalid_temperature_request():
    """Invalid request with out-of-range temperature."""
    return {
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 5.0
    }
