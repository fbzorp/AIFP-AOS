import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.content_item import ContentItemModel
from apps.agents.specialized import TechnicalContentAgent, FounderContentAgent, ComplianceBrandAgent

# Setup in-memory SQLite for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

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

@pytest.mark.asyncio
async def test_technical_content_agent():
    agent = TechnicalContentAgent()
    
    # Pre-populate a content item
    with mock_get_sync_session() as session:
        item = ContentItemModel(id="test-123", title="SDK Tutorial", channel="Blog", status="planned")
        session.add(item)
        session.commit()

    mock_llm_response = {"body": "Real technical content for AiFinPay SDK."}
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": "test-123"})
        
        assert result["outcome"] == "tutorial_generated"
        
        with mock_get_sync_session() as session:
            db_item = session.query(ContentItemModel).filter_by(id="test-123").first()
            assert db_item.body == "Real technical content for AiFinPay SDK."
            assert db_item.status == "draft"
            assert db_item.author_agent == "Technical Content"

@pytest.mark.asyncio
async def test_founder_content_agent():
    agent = FounderContentAgent()
    
    # Pre-populate a content item
    with mock_get_sync_session() as session:
        item = ContentItemModel(id="test-456", title="Future of AI", channel="X", status="planned")
        session.add(item)
        session.commit()

    mock_llm_response = {
        "variants": [
            {"audience": "Investors", "text": "AiFinPay is scaling fast."},
            {"audience": "Developers", "text": "Build on AiFinPay today."}
        ]
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": "test-456"})
        
        assert result["outcome"] == "founder_draft_ready"
        
        with mock_get_sync_session() as session:
            db_item = session.query(ContentItemModel).filter_by(id="test-456").first()
            assert len(db_item.variants) == 2
            assert db_item.status == "draft"
            assert db_item.author_agent == "Founder Content"

@pytest.mark.asyncio
async def test_compliance_brand_agent_approved():
    agent = ComplianceBrandAgent()
    
    # Pre-populate a content item
    with mock_get_sync_session() as session:
        item = ContentItemModel(id="test-789", title="Safe Post", channel="X", body="Safe content.", status="draft")
        session.add(item)
        session.commit()

    mock_llm_response = {"status": "approved", "reason": "All good."}
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": "test-789"})
        
        assert result["status"] == "approved"
        
        with mock_get_sync_session() as session:
            db_item = session.query(ContentItemModel).filter_by(id="test-789").first()
            assert db_item.compliance_status == "approved"
            assert db_item.status == "pending_review"

@pytest.mark.asyncio
async def test_compliance_brand_agent_rejected():
    agent = ComplianceBrandAgent()
    
    # Pre-populate a content item
    with mock_get_sync_session() as session:
        item = ContentItemModel(id="test-bad", title="Bad Post", channel="X", body="Guaranteed 1000% returns!", status="draft")
        session.add(item)
        session.commit()

    mock_llm_response = {"status": "rejected", "reason": "Financial advice violation."}
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": "test-bad"})
        
        assert result["status"] == "rejected"
        
        with mock_get_sync_session() as session:
            db_item = session.query(ContentItemModel).filter_by(id="test-bad").first()
            assert db_item.compliance_status == "rejected"
            assert db_item.status == "rejected"
