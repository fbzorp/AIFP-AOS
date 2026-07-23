import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from apps.api.main import app

client = TestClient(app)

@pytest.fixture
def mock_orchestrator_result():
    return {
        "agent": "Growth Orchestrator",
        "outcome": "campaign_dispatched",
        "campaign_id": "camp-123",
        "tasks": ["task-1", "task-2"],
        "status": "executing"
    }

def test_create_campaign_endpoint(mock_orchestrator_result):
    """
    Test POST /api/v1/campaigns returns the correct response from the orchestrator.
    """
    mock_agent = MagicMock()
    mock_agent.execute = MagicMock(return_value=mock_orchestrator_result)
    
    with patch('apps.api.routers.system.get_agent', return_value=mock_agent):
        response = client.post(
            "/api/v1/campaigns",
            json={"objective": "Increase social media presence"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == "camp-123"
        assert len(data["tasks"]) == 2
        assert data["outcome"] == "campaign_dispatched"
        mock_agent.execute.assert_called_once_with({"objective": "Increase social media presence"})

def test_create_campaign_agent_not_found():
    """
    Test POST /api/v1/campaigns returns 500 if orchestrator is missing.
    """
    with patch('apps.api.routers.system.get_agent', return_value=None):
        response = client.post(
            "/api/v1/campaigns",
            json={"objective": "Test objective"}
        )
        assert response.status_code == 500
        assert "not found" in response.json()["detail"]
