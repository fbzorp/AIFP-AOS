import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.agents.specialized import ContentStrategyAgent

# Setup in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(bind=engine)

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
async def test_content_strategy_produces_linked_drafts():
    agent = ContentStrategyAgent()
    
    # Pre-seed a source
    with mock_get_sync_session() as session:
        source = SourceModel(
            id="source-123",
            url="https://aifinpay.com",
            url_hash="hash123",
            title="AiFinPay Growth",
            summary="Intelligence about growth.",
            relevance_score=0.9,
            topic="Fintech"
        )
        session.add(source)
        session.commit()

    mock_llm_response = {
        "items": [
            {
                "title": "New Fintech Strategy",
                "channel": "X",
                "objective": "Brand awareness",
                "target_audience": "Founders",
                "format": "Thread",
                "cta": "Sign up",
                "kpi": "Engagement",
                "source_id": "source-123"
            }
        ]
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"objective": "Grow brand"})
        
        assert len(result["items"]) == 1
        
        # Verify persistence and linking
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id=result["items"][0]).first()
            assert item is not None
            assert item.status == "draft"
            assert item.source_id == "source-123"
            assert item.author_agent == "Content Strategy"
            assert item.objective == "Brand awareness"
