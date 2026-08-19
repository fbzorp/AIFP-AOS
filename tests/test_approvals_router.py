"""Tests for approvals router to improve coverage."""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


def test_approvals_unauthorized():
    """Test approvals endpoint without authentication."""
    client = TestClient(app)
    response = client.get("/api/approvals")
    assert response.status_code in [401, 403, 404]


def test_approvals_post_unauthorized():
    """Test approval creation without authentication."""
    client = TestClient(app)
    response = client.post("/api/approvals", json={"content_id": "test"})
    assert response.status_code in [401, 403, 404, 422]


def test_approvals_detail_unauthorized():
    """Test approval detail without authentication."""
    client = TestClient(app)
    response = client.get("/api/approvals/test-id")
    assert response.status_code in [401, 403, 404]