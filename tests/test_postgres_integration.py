"""Postgres-backed integration tests for features requiring pgvector."""
import pytest
import os
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from apps.models.base import Base
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.agents.specialized import ContentStrategyAgent

# Only run these tests if we have a real Postgres connection
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="Postgres-backed integration test requires DATABASE_URL with postgresql://"
)


@pytest.fixture(scope="module")
def postgres_engine():
    """Create a Postgres engine for integration tests."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")
    
    # Convert async URL to sync URL for testing
    if database_url.startswith("postgresql+asyncpg"):
        database_url = database_url.replace("postgresql+asyncpg", "postgresql")
    
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    
    # Ensure pgvector extension is enabled
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(postgres_engine):
    """Create a database session for each test."""
    TestingSessionLocal = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_content_strategy_semantic_retrieval_postgres(db_session):
    """Test that ContentStrategyAgent uses semantic retrieval with real pgvector."""
    agent = ContentStrategyAgent()
    
    # Pre-seed multiple sources with embeddings
    relevant_embedding = [0.9] * 384  # High similarity to "growth"
    irrelevant_embedding = [0.1] * 384  # Low similarity
    
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
    db_session.add(source1)
    db_session.add(source2)
    db_session.flush()
    
    # Set embeddings via raw SQL using proper pgvector casting
    db_session.execute(
        text("UPDATE sources SET embedding = cast(:embedding as vector) WHERE id = :source_id"),
        {"embedding": str(relevant_embedding), "source_id": "source-relevant"}
    )
    db_session.execute(
        text("UPDATE sources SET embedding = cast(:embedding as vector) WHERE id = :source_id"),
        {"embedding": str(irrelevant_embedding), "source_id": "source-irrelevant"}
    )
    db_session.commit()
    
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
         patch("apps.agents.specialized.get_sync_session", return_value=db_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"objective": "Grow brand"})
        
        assert len(result["items"]) == 1
        
        # Verify persistence and linking - the content item should be linked to the semantically-retrieved source
        # result["items"][0] is the content item ID (UUID), not the source ID
        item = db_session.query(ContentItemModel).filter_by(id=result["items"][0]).first()
        assert item is not None
        assert item.status == "draft"
        assert item.source_id == "source-relevant"
        assert item.author_agent == "Content Strategy"
        assert item.objective == "Brand awareness"
