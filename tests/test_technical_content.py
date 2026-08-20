import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.content_item import ContentItemModel
from apps.models.source import SourceModel
from apps.agents.specialized import TechnicalContentAgent

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
async def test_technical_content_verification_passes():
    """Test that content with verifiable technical claims passes verification."""
    agent = TechnicalContentAgent()
    
    # Create a test content item
    with mock_get_sync_session() as session:
        source = SourceModel(
            url="https://example.com/docs",
            url_hash="test_hash",
            title="Autonomous Publishing Documentation",
            raw_content="Official documentation about autonomous publishing endpoints."
        )
        session.add(source)
        session.flush()
        
        content_item = ContentItemModel(
            title="How to Use Autonomous Publishing",
            channel="moltbook",
            status="draft",
            objective="Explain basic autonomous publishing usage",
            source_id=source.id
        )
        session.add(content_item)
        session.commit()
        content_item_id = content_item.id
    
    # Mock LLM response with verifiable technical content
    mock_llm_response = {
        "body": "To use the autonomous publishing system, you can use the /api/v1/content endpoint to create content and /api/v1/approvals for approval workflow. The system supports multi_channel_publishing and content_generation features."
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": content_item_id})
        
        assert result["outcome"] == "tutorial_generated"
        # Should verify since it mentions valid endpoints and features
        assert result["verification_status"] in ["verified", "pending"]  # May be verified if claims found
        
        # Verify content item was updated with verification status
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id=content_item_id).first()
            assert item.technical_verification_status in ["verified", "pending"]
            assert item.status == "draft"  # Should remain draft for review

@pytest.mark.asyncio
async def test_technical_content_verification_fails():
    """Test that content with unverifiable technical claims fails verification and gets flagged."""
    agent = TechnicalContentAgent()
    
    # Create a test content item
    with mock_get_sync_session() as session:
        source = SourceModel(
            url="https://example.com/docs",
            url_hash="test_hash",
            title="Test Docs",
            raw_content="Some documentation content."
        )
        session.add(source)
        session.flush()
        
        content_item = ContentItemModel(
            title="Advanced Autonomous Publishing Features",
            channel="moltbook",
            status="draft",
            objective="Show advanced features",
            source_id=source.id
        )
        session.add(content_item)
        session.commit()
        content_item_id = content_item.id
    
    # Mock LLM response with unverifiable technical claims (invented endpoint and unsupported network)
    mock_llm_response = {
        "body": "The autonomous publishing system supports /api/v2/payments/create for payment processing and ethereum network for blockchain transactions."
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": content_item_id})
        
        assert result["outcome"] == "tutorial_generated"
        # Should fail verification due to invented endpoint and unsupported network
        assert result["verification_status"] == "failed"
        assert "verification_status" in result
        assert "verification_details" in result
        
        # Verify content item was flagged
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id=content_item_id).first()
            assert item.technical_verification_status == "flagged"
            assert item.status == "draft"  # Should remain draft for human review

@pytest.mark.asyncio
async def test_technical_content_no_claims_pending():
    """Test that content without technical claims gets pending status."""
    agent = TechnicalContentAgent()
    
    # Create a test content item
    with mock_get_sync_session() as session:
        source = SourceModel(
            url="https://example.com/docs",
            url_hash="test_hash",
            title="Test Docs",
            raw_content="General content about publishing."
        )
        session.add(source)
        session.flush()
        
        content_item = ContentItemModel(
            title="Publishing Overview",
            channel="moltbook",
            status="draft",
            objective="General overview",
            source_id=source.id
        )
        session.add(content_item)
        session.commit()
        content_item_id = content_item.id
    
    # Mock LLM response without technical claims
    mock_llm_response = {
        "body": "This is a general overview of publishing systems without specific technical details."
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": content_item_id})
        
        assert result["outcome"] == "tutorial_generated"
        # Should be pending since no technical claims found
        assert result["verification_status"] == "pending"
        assert "verification_status" in result
        assert "verification_details" in result
        
        # Verify content item status
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id=content_item_id).first()
            assert item.technical_verification_status == "pending"
            assert item.status == "draft"
