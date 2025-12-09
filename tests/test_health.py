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
