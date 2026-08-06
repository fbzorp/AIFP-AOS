import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.agents.specialized import SEOContentAgent

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
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_seo_content_agent_generates_seo_content():
    agent = SEOContentAgent()
    
    # Pre-seed a source
    with mock_get_sync_session() as session:
        source = SourceModel(
            id="source-seo-123",
            url="https://aifinpay.com/blog/seo-guide",
            url_hash="seo-hash123",
            title="SEO Guide for Fintech",
            summary="Comprehensive SEO strategies for fintech companies.",
            relevance_score=0.95,
            topic="SEO"
        )
        session.add(source)
        content_item = ContentItemModel(
            id="content-seo-123",
            title="SEO Best Practices for Fintech",
            objective="Improve search rankings",
            channel="google",
            format="article",
            source_id="source-seo-123"
        )
        session.add(content_item)
        session.commit()

    mock_llm_response = {
        "seo_title_tag": "SEO Best Practices for Fintech Companies - Complete Guide",
        "meta_description": "Learn proven SEO strategies for fintech companies to improve search rankings and drive organic traffic. Expert tips and actionable insights.",
        "keywords": ["fintech seo", "search optimization", "financial marketing"],
        "h1": "SEO Best Practices for Fintech Companies",
        "h2_subheadings": ["Keyword Research", "On-Page Optimization", "Technical SEO", "Content Strategy"],
        "body": "This is the complete SEO-optimized article body covering all best practices for fintech companies..."
    }
    
    with patch("apps.agents.specialized.complete_json", new_callable=AsyncMock) as mock_llm, \
         patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session), \
         patch("apps.core.models.llm.settings") as mock_settings:
        
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_llm.return_value = mock_llm_response
        
        result = await agent.execute({"content_item_id": "content-seo-123"})
        
        assert result["agent"] == "SEO Content"
        assert result["outcome"] == "seo_content_generated"
        assert result["item_id"] == "content-seo-123"
        
        # Verify persistence and SEO metadata
        with mock_get_sync_session() as session:
            item = session.query(ContentItemModel).filter_by(id="content-seo-123").first()
            assert item is not None
            assert item.status == "draft"
            assert item.author_agent == "SEO Content"
            assert item.body == "This is the complete SEO-optimized article body covering all best practices for fintech companies..."
            
            # Verify SEO metadata stored in variants
            assert item.variants is not None
            assert item.variants["seo_title_tag"] == "SEO Best Practices for Fintech Companies - Complete Guide"
            assert item.variants["meta_description"] == "Learn proven SEO strategies for fintech companies to improve search rankings and drive organic traffic. Expert tips and actionable insights."
            assert item.variants["keywords"] == ["fintech seo", "search optimization", "financial marketing"]
            assert item.variants["h1"] == "SEO Best Practices for Fintech Companies"
            assert item.variants["h2_subheadings"] == ["Keyword Research", "On-Page Optimization", "Technical SEO", "Content Strategy"]

@pytest.mark.asyncio
async def test_seo_content_agent_handles_missing_item():
    agent = SEOContentAgent()
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        result = await agent.execute({"content_item_id": "nonexistent-id"})
        
        assert result["error"] == "Content item not found"

@pytest.mark.asyncio
async def test_seo_content_agent_capabilities():
    agent = SEOContentAgent()
    capabilities = agent.get_capabilities()
    
    assert capabilities["purpose"] == "Creates Google-optimized content with SEO metadata..."
    assert "seo_optimization" in capabilities["tools"]
    assert capabilities["outputs"] == ["draft"]
    assert capabilities["policies"] == ["seo_best_practices"]
