import pytest
from unittest.mock import MagicMock, patch
from apps.models.task import TaskModel
from apps.workers.tasks import run_agent_task

@pytest.fixture
def mock_session():
    session = MagicMock()
    return session

@pytest.fixture
def mock_task():
    return TaskModel(id="task-123", task_type="Market Intelligence", status="pending", input_data={"topic": "test"})

def test_task_idempotency_succeeded(mock_session, mock_task):
    """Running a succeeded task should return early without re-executing."""
    mock_task.status = "succeeded"
    mock_session.query().filter().first.return_value = mock_task
    
    with patch('apps.workers.tasks.get_sync_session', return_value=MagicMock(__enter__=lambda _: mock_session)):
        with patch('apps.workers.tasks.get_agent') as mock_get_agent:
            run_agent_task("task-123")
            mock_get_agent.assert_not_called()

def test_task_execution_flow(mock_session, mock_task):
    """Running a pending task should update status and record audit events."""
    mock_session.query().filter().first.return_value = mock_task
    
    mock_agent = MagicMock()
    mock_agent.name = "Market Intelligence"
    mock_agent.execute = MagicMock(return_value={"result": "ok"})
    
    with patch('apps.workers.tasks.get_sync_session', return_value=MagicMock(__enter__=lambda _: mock_session)):
        with patch('apps.workers.tasks.get_agent', return_value=mock_agent):
            with patch('apps.workers.tasks.asyncio.run', return_value={"result": "ok"}):
                run_agent_task("task-123")
                
                assert mock_task.status == "succeeded"
                assert mock_task.result == {"result": "ok"}
                # Check if record_event was called (at least for started and succeeded)
                assert mock_session.add.call_count >= 2
