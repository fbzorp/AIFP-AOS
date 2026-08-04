import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from apps.models.base import Base, get_sync_session, get_db
from apps.models.content_item import ContentItemModel
from apps.models.engagement_proposal import EngagementProposalModel
from apps.models.task import TaskModel
from apps.agents.specialized import GrowthOrchestratorAgent, CommunityEngagementAgent
from apps.api.main import app
from apps.api.auth import create_test_token

# Setup in-memory SQLite for testing with proper connection pooling
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class AsyncSessionMock:
    def __init__(self, sync_session):
        self.sync_session = sync_session
    async def execute(self, query):
        return self.sync_session.execute(query)
    def add(self, obj):
        return self.sync_session.add(obj)
    def flush(self):
        self.sync_session.flush()
        class AwaitableNone:
            def __await__(self):
                async def _wrap(): return None
                return _wrap().__await__()
        return AwaitableNone()
    async def commit(self):
        return self.sync_session.commit()
    async def rollback(self):
        return self.sync_session.rollback()
    async def close(self):
        return self.sync_session.close()
    def scalars(self):
        return self
    def first(self):
        return self

async def override_get_db():
    sync_session = TestingSessionLocal()
    async_session = AsyncSessionMock(sync_session)
    try:
        yield async_session
    finally:
        await async_session.close()

@patch("apps.agents.specialized.get_sync_session")
@patch("apps.core.orchestrator.engine.Orchestrator.create_campaign")
@pytest.mark.asyncio
async def test_gap_b_orchestrator_enqueues_discovered_discussions(
    mock_create_campaign,
    mock_get_session,
):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    mock_create_campaign.return_value = {"campaign_id": "camp_1", "tasks": []}
    mock_client = MagicMock()
    mock_client.list_discussions = AsyncMock(return_value=[])
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    agent = GrowthOrchestratorAgent()
    with patch("apps.agents.specialized.MoltbookClient", return_value=mock_context):
        await agent.execute({"objective": "Test Gap B"})

    # Verify Community Engagement is included and receives only discovered records.
    args, kwargs = mock_create_campaign.call_args
    steps = args[1]
    agent_names = [s["agent"] for s in steps]
    assert "Community Engagement" in agent_names

    engagement_step = next(s for s in steps if s["agent"] == "Community Engagement")
    assert engagement_step["input"] == {"discussions": []}

@patch("apps.agents.specialized.get_sync_session")
@patch("apps.agents.specialized.complete_json")
@pytest.mark.asyncio
async def test_gap_b_agent_produces_proposals(mock_complete_json, mock_get_session):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    
    mock_complete_json.return_value = {
        "discussion_summary": "Summary",
        "proposed_reply": "Reply"
    }
    
    agent = CommunityEngagementAgent()
    input_data = {
        "discussions": [{"url": "http://test", "submolt": "general", "content": "Hello"}]
    }
    
    await agent.execute(input_data)
    
    # Verify proposal committed
    proposal = session.query(EngagementProposalModel).first()
    assert proposal is not None
    assert proposal.status == "proposed"

@pytest.mark.asyncio
async def test_gap_c_approval_sets_scheduled_at():
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = create_test_token(role="smm_manager")
        headers = {"Authorization": f"Bearer {token}"}
        
        with TestingSessionLocal() as session:
            # Create content
            content = ContentItemModel(
                id="gap-c-1",
                title="Scheduled Post",
                channel="general",
                status="draft"
            )
            session.add(content)
            session.commit()
            
            # Approve via API
            response = await ac.post("/api/v1/content/gap-c-1/approve", json={"approved_by": "Tester"}, headers=headers)
            assert response.status_code == 200
            
            # Verify scheduled_at is set
            # Use a fresh session to verify the commit from the API
            with TestingSessionLocal() as fresh_session:
                updated_content = fresh_session.query(ContentItemModel).filter(ContentItemModel.id == "gap-c-1").first()
                assert updated_content.status == "approved"
                assert updated_content.scheduled_at is not None
            
            # Verify it appears in calendar
            cal_response = await ac.get("/api/v1/calendar", headers=headers)
            assert cal_response.status_code == 200
            cal_data = cal_response.json()
            assert any(item["id"] == "gap-c-1" for item in cal_data)
    
    app.dependency_overrides.clear()
