"""Tests for prometheus metrics endpoint."""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


def test_metrics_endpoint():
    """Test the /metrics endpoint returns prometheus data."""
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type():
    """Test the /metrics endpoint returns correct content type."""
    client = TestClient(app)
    response = client.get("/metrics")
    assert "text/plain" in response.headers.get("content-type", "")


def test_root_endpoint():
    """Test the root endpoint returns expected response."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data