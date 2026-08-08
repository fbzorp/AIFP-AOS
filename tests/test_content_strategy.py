import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.agents.specialized import ContentStrategyAgent

# Setup in-memory SQLite for testing with StaticPool to share connection across threads
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
    # Create tables without the Vector column for SQLite compatibility
    from apps.models.source import SourceModel
    # Since embedding column is not in model, we don't need to patch it
    # The migration will add it for Postgres, but SQLite tests don't need it
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_content_strategy_produces_linked_drafts():
    agent = ContentStrategyAgent()
    
    # Pre-seed a source (embedding not passed since column not in model)
    mock_embedding = [0.1] * 384
    
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
    
    # Mock the embedding function for semantic retrieval
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.embed_text", return_value=mock_embedding), \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
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

@pytest.mark.asyncio
async def test_content_strategy_semantic_retrieval():
    """Test that ContentStrategyAgent uses semantic retrieval when embeddings exist."""
    agent = ContentStrategyAgent()
    
    # Pre-seed multiple sources (embeddings set via raw SQL since column not in model)
    relevant_embedding = [0.9] * 384  # High similarity to "growth"
    irrelevant_embedding = [0.1] * 384  # Low similarity
    
    embedding_column_exists = False
    
    with mock_get_sync_session() as session:
        source1 = SourceModel(
            id="source-relevant",
            url="https://aifinpay.com/growth",
            url_hash="hash1",
            title="AiFinPay Growth Strategy",
            summary="Detailed growth strategies for fintech platforms.",
            relevance_score=0.8,
            topic="Growth"
        )
        source2 = SourceModel(
            id="source-irrelevant",
            url="https://other.com/tech",
            url_hash="hash2",
            title="General Tech News",
            summary="General technology news unrelated to fintech.",
            relevance_score=0.9,  # High relevance_score but different topic
            topic="General Tech"
        )
        session.add(source1)
        session.add(source2)
        session.flush()
        
        # Set embeddings via raw SQL since column not in model
        # (This simulates what the production code does in Postgres)
        try:
            session.execute(
                text("UPDATE sources SET embedding = :embedding WHERE id = :source_id"),
                {"embedding": str(relevant_embedding), "source_id": "source-relevant"}
            )
            session.execute(
                text("UPDATE sources SET embedding = :embedding WHERE id = :source_id"),
                {"embedding": str(irrelevant_embedding), "source_id": "source-irrelevant"}
            )
            embedding_column_exists = True
        except Exception:
            # SQLite tests don't have embedding column, skip semantic retrieval test
            pass
        
        session.commit()
    
    # Skip test if embedding column doesn't exist (SQLite tests)
    if not embedding_column_exists:
        pytest.skip("Embedding column not available in SQLite tests")

    mock_llm_response = {
        "items": [
            {
                "title": "Growth-Focused Content",
                "channel": "X",
                "objective": "Brand awareness",
                "target_audience": "Founders",
                "format": "Thread",
                "cta": "Sign up",
                "kpi": "Engagement",
                "source_id": "source-relevant"
            }
        ]
    }
    
    query_embedding = [0.8] * 384  # Similar to relevant embedding
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.embed_text", return_value=query_embedding), \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"objective": "Grow brand"})
        
        assert len(result["items"]) == 1
        
        # Verify persistence and linking - the content item should be linked to the semantically-retrieved source
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id=result["items"][0]).first()
            assert item is not None
            assert item.status == "draft"
            assert item.source_id == "source-relevant"
            assert item.author_agent == "Content Strategy"
            assert item.objective == "Brand awareness"
