import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.models.audit_event import AuditEventModel
from apps.core.policy.engine import PolicyEngine, compute_draft_hash
from apps.workers.tasks import publish_content
from apps.api.main import app
from httpx import AsyncClient, ASGITransport

# Setup in-memory SQLite for testing with StaticPool to share connection across threads
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class AsyncSessionMock:
    """A mock to wrap sync session to look like an async session for FastAPI tests."""
    def __init__(self, sync_session):
        self.sync_session = sync_session
    
    async def execute(self, query):
        return self.sync_session.execute(query)
    
    def add(self, obj):
        return self.sync_session.add(obj)
    
    async def flush(self):
        return self.sync_session.flush()
    
    async def commit(self):
        return self.sync_session.commit()
    
    async def rollback(self):
        return self.sync_session.rollback()
    
    async def close(self):
        return self.sync_session.close()

@contextmanager
def mock_get_sync_session():
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_approval_logic():
    with mock_get_sync_session() as session:
        # 1. Create a draft
        content = ContentItemModel(
            id="test-content",
            title="Test Post",
            body="Hello AiFinPay",
            channel="X",
            status="draft"
        )
        session.add(content)
        session.commit()
        
        draft_hash = compute_draft_hash(content)
        
        # 2. Approve it
        approval = ApprovalModel(
            content_id=content.id,
            draft_hash=draft_hash,
            status="approved",
            approved_by="Human",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        session.add(approval)
        content.status = "approved"
        session.commit()
        
        # 3. Validate via PolicyEngine
        engine_policy = PolicyEngine()
        assert engine_policy.validate_approval(session, approval.id, draft_hash) is True
        
        # 4. Tamper with hash -> fail
        assert engine_policy.validate_approval(session, approval.id, "wrong-hash") is False
        
        # 5. Expired -> fail
        approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session.commit()
        assert engine_policy.validate_approval(session, approval.id, draft_hash) is False

def test_rejection_logic():
    with mock_get_sync_session() as session:
        content = ContentItemModel(
            id="test-reject",
            title="Bad Post",
            channel="X",
            status="draft"
        )
        session.add(content)
        session.commit()
        
        # Reject
        approval = ApprovalModel(
            content_id=content.id,
            draft_hash=compute_draft_hash(content),
            status="rejected",
            approved_by="Human"
        )
        session.add(approval)
        content.status = "rejected"
        session.commit()
        
        engine_policy = PolicyEngine()
        assert engine_policy.validate_approval(session, approval.id, compute_draft_hash(content)) is False

@patch("apps.workers.tasks.get_sync_session", side_effect=mock_get_sync_session)
def test_publish_gate(mock_session):
    with mock_get_sync_session() as session:
        content = ContentItemModel(
            id="content-1",
            title="Title",
            body="Body",
            channel="X",
            status="draft"
        )
        session.add(content)
        session.commit()
        
        draft_hash = compute_draft_hash(content)
        
        # 1. Try to publish draft -> Denied
        with pytest.raises(ValueError, match="must be approved"):
            publish_content("content-1", "no-appr", draft_hash)
            
        # 2. Approve
        approval = ApprovalModel(
            id="appr-1",
            content_id="content-1",
            draft_hash=draft_hash,
            status="approved",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        session.add(approval)
        content.status = "approved"
        session.commit()
        
        # 3. Publish approved -> Ready
        result = publish_content("content-1", "appr-1", draft_hash)
        assert result["status"] == "ready_for_integration"
        
        # 4. Reject and try to publish -> Denied
        content.status = "rejected"
        session.commit()
        with pytest.raises(ValueError, match="must be approved"):
            publish_content("content-1", "appr-1", draft_hash)

async def override_get_db():
    sync_session = TestingSessionLocal()
    async_session = AsyncSessionMock(sync_session)
    try:
        yield async_session
    finally:
        await async_session.close()

@pytest.mark.asyncio
async def test_api_approval_and_publish_trigger():
    # Use the FastAPI test client with the mocked DB session
    from apps.models.base import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    # Mock Redis to avoid connection errors in test environment
    with patch("apps.api.main.Redis.from_url") as mock_redis:
        mock_redis.return_value.ping.return_value = True
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with mock_get_sync_session() as session:
                # 1. Create draft
                content = ContentItemModel(
                    id="api-content-1",
                    title="API Test",
                    body="Hello",
                    channel="X",
                    status="draft"
                )
                session.add(content)
                session.commit()
                
                # 2. Approve via API
                response = await ac.post("/api/v1/content/api-content-1/approve", json={"approved_by": "Tester"})
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "approved"
                
                # 3. Trigger Publish via API
                # Mock the dramatiq .send method
                with patch("apps.workers.tasks.publish_content.send") as mock_send:
                    pub_response = await ac.post("/api/v1/content/api-content-1/publish")
                    assert pub_response.status_code == 200
                    assert pub_response.json()["status"] == "publish_enqueued"
                    mock_send.assert_called_once()
    
    # Clean up
    app.dependency_overrides.clear()
