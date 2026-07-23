import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from apps.api.main import app
from apps.models.base import get_sync_session
from apps.models.audit_event import AuditEventModel
from apps.models.task import TaskModel
from apps.core.orchestrator.engine import Orchestrator

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
    # Use AsyncMock because execute is awaited
    mock_agent.execute = AsyncMock(return_value=mock_orchestrator_result)
    
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

def test_orchestrator_audit_trail():
    """
    Verify that Orchestrator.create_campaign records task_enqueued events.
    """
    session = MagicMock()
    # Mocking the flush to assign IDs to campaign and tasks
    def mock_flush():
        # Find campaign and tasks in session.add calls
        for call in session.add.call_args_list:
            obj = call[0][0]
            if not hasattr(obj, 'id') or obj.id is None:
                import uuid
                obj.id = str(uuid.uuid4())

    session.flush.side_effect = mock_flush
    
    # Mock dramatiq .send
    with patch('apps.workers.tasks.run_agent_task.send') as mock_send:
        orch = Orchestrator(session)
        steps = [
            {"agent": "Market Intelligence", "input": {"topic": "test"}},
            {"agent": "Content Strategy", "input": {"objective": "test"}}
        ]
        
        result = orch.create_campaign("Test Objective", steps)
        
        # Verify result structure
        assert result["campaign_id"] is not None
        assert len(result["tasks"]) == 2
        
        # Verify dramatiq was called twice
        assert mock_send.call_count == 2
        
        # Verify audit events were recorded
        # We expect: 1 campaign_created + 2 task_enqueued = 3 calls to record_event (which calls session.add)
        # record_event is imported in engine.py, we can check session.add calls
        added_objects = [call[0][0] for call in session.add.call_args_list]
        audit_events = [obj for obj in added_objects if isinstance(obj, AuditEventModel)]
        
        # 1 campaign_created + 2 task_enqueued
        assert len(audit_events) == 3
        
        event_types = [e.event_type for e in audit_events]
        assert "campaign_created" in event_types
        assert event_types.count("task_enqueued") == 2
        
        # Check metadata for one enqueued event
        enqueued_event = next(e for e in audit_events if e.event_type == "task_enqueued")
        assert "task_id" in enqueued_event.metadata_json
        assert "campaign_id" in enqueued_event.metadata_json
        assert enqueued_event.metadata_json["campaign_id"] == result["campaign_id"]
