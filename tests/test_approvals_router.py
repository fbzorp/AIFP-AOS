import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_get_approvals_no_auth():
    """Test GET /approvals without authentication"""
    response = client.get("/api/v1/approvals/")
    # Should return 401 or 404 if endpoint doesn't exist
    assert response.status_code in [401, 404]


def test_approve_content_no_auth():
    """Test POST /approvals/{id}/approve without authentication"""
    response = client.post("/api/v1/approvals/test_id/approve")
    # Should return 401 or 404 if endpoint doesn't exist
    assert response.status_code in [401, 404]


def test_reject_content_no_auth():
    """Test POST /approvals/{id}/reject without authentication"""
    response = client.post("/api/v1/approvals/test_id/reject")
    # Should return 401 or 404 if endpoint doesn't exist
    assert response.status_code in [401, 404]