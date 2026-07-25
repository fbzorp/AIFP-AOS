import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.models.base import Base, get_sync_session
from apps.models.task import TaskModel
from apps.models.content_item import ContentItemModel
from apps.models.source import SourceModel
from apps.workers.tasks import run_agent_task
from apps.core.orchestrator.engine import Orchestrator

# Setup in-memory SQLite for testing with multi-thread support
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@patch("apps.workers.tasks.get_sync_session")
@patch("apps.agents.specialized.get_sync_session")
@patch("apps.agents.specialized.complete_json")
@patch("apps.workers.tasks.run_agent_task.send")
def test_news_to_content_orchestration_flow(mock_send, mock_complete_json, mock_agent_session, mock_worker_session, db_session):
    # Setup mocks
    mock_worker_session.return_value.__enter__.return_value = db_session
    mock_agent_session.return_value.__enter__.return_value = db_session
    
    # Mock LLM responses for each agent
    def side_effect(model, system_prompt, user_content, schema_hint):
        if "weekly content plan" in system_prompt.lower():
            return {
                "items": [
                    {
                        "channel": "X",
                        "target_audience": "Developers",
                        "objective": "Showcase SDK",
                        "format": "Technical tutorial",
                        "cta": "Try SDK",
                        "kpi": "installs",
                        "source_id": "src_1",
                        "title": "How to use AiFinPay SDK"
                    },
                    {
                        "channel": "LinkedIn",
                        "target_audience": "Investors",
                        "objective": "Growth update",
                        "format": "Founder insight",
                        "cta": "Contact us",
                        "kpi": "leads",
                        "source_id": "src_1",
                        "title": "AiFinPay Q3 Growth"
                    }
                ]
            }
        elif "technical tutorial" in system_prompt.lower():
            return {"body": "This is a technical tutorial about the SDK."}
        elif "high-impact leadership post" in system_prompt.lower():
            return {"variants": [{"audience": "Investors", "text": "We are growing fast!"}]}
        elif "compliance and brand violations" in system_prompt.lower():
            return {"status": "approved", "reason": "Looks good"}
        return {}

    mock_complete_json.side_effect = side_effect

    # 1. Start with a Content Strategy task
    strategy_task = TaskModel(
        task_type="Content Strategy",
        input_data={"objective": "Test Campaign"},
        status="pending"
    )
    db_session.add(strategy_task)
    db_session.commit()

    # Run the strategy task
    run_agent_task(strategy_task.id)

    # Assertions for Strategy
    assert strategy_task.status == "succeeded"
    items = db_session.query(ContentItemModel).all()
    assert len(items) == 2
    
    # Verify two new tasks were enqueued (one Technical, one Founder)
    # mock_send.call_count should be 2 now
    assert mock_send.call_count == 2
    
    # Get the new task IDs from the calls
    generation_task_ids = [call.args[0] for call in mock_send.call_args_list]
    
    # 2. Run the generation tasks
    for task_id in generation_task_ids:
        run_agent_task(task_id)
        
    # After generation, each should have enqueued a Compliance task
    # Total calls: 2 (generation) + 2 (compliance) = 4
    assert mock_send.call_count == 4
    compliance_task_ids = [call.args[0] for call in mock_send.call_args_list[2:]]
    
    # 3. Run compliance tasks
    for task_id in compliance_task_ids:
        run_agent_task(task_id)
        
    # Final assertions
    for item in items:
        db_item = db_session.query(ContentItemModel).filter(ContentItemModel.id == item.id).first()
        if "Technical" in db_item.title or "SDK" in db_item.title:
            assert db_item.body is not None
            assert db_item.author_agent == "Technical Content"
        else:
            assert db_item.variants is not None
            assert db_item.author_agent == "Founder Content"
        
        assert db_item.compliance_status == "approved"
        assert db_item.status == "pending_review" # Approved items go to human review queue
