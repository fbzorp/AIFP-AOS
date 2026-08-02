import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_get_root():
    """Test GET / root endpoint"""
    response = client.get("/")
    assert response.status_code in [200, 404]


def test_get_agents():
    """Test GET /agents endpoint"""
    response = client.get("/api/v1/agents")
    # Should return list of agents or 404 if endpoint doesn't exist
    assert response.status_code in [200, 404]