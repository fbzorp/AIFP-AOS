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
        "body": "To use the autonomous publishing system, you can create content and submit it for approval. The system supports multiple channels including X, Telegram, and Moltbook."
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": content_item_id})
        
        assert result["outcome"] == "tutorial_generated"
        # Technical verification disabled after payment removal - always pending
        assert result["verification_status"] == "pending"
        
        # Verify content item was updated with verification status
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id=content_item_id).first()
            assert item.technical_verification_status == "pending"
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
    
    # Mock LLM response with unverifiable technical claims
    mock_llm_response = {
        "body": "The autonomous publishing system supports fake_testnet for test deployments."
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": content_item_id})
        
        assert result["outcome"] == "tutorial_generated"
        # Technical verification disabled after payment removal - always pending
        assert result["verification_status"] == "pending"
        assert "verification_status" in result
        assert "verification_details" in result

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
        # Technical verification disabled after payment removal - always pending
        assert result["verification_status"] == "pending"
        assert "verification_status" in result
        assert "verification_details" in result
