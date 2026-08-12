"""Tests for Marketing Activity & Evidence Registry API endpoints."""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


class TestMarketingActivityAPI:
    """Tests for Marketing Activity API endpoints."""
    
    def test_get_marketing_activity_unauthorized(self):
        """Test that marketing activity endpoint requires authentication."""
        response = client.get("/api/v1/marketing/activity")
        # Should return 401 when no Authorization header is supplied
        assert response.status_code == 401
    
    def test_get_marketing_activity_detail_unauthorized(self):
        """Test that marketing activity detail endpoint requires authentication."""
        response = client.get("/api/v1/marketing/activity/test-id")
        # Should return 401 when no Authorization header is supplied
        assert response.status_code == 401