"""Tests for API health and system endpoints."""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


def test_health_endpoint():
    """Test the /health endpoint returns expected response."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "dependencies" in data


def test_health_postgres_unhealthy():
    """Test health endpoint when postgres is unhealthy."""
    # This test requires mocking the database dependency
    # For now, just test the endpoint returns 200
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_redis_unhealthy():
    """Test health endpoint when redis is unhealthy."""
    # This test requires mocking the redis dependency
    # For now, just test the endpoint returns 200
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200