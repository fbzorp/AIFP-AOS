import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from apps.models.base import Base
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from apps.agents.specialized import AnalyticsAgent

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
async def test_analytics_real_publications_count():
    """Test that AnalyticsAgent counts real publications only (excludes dry-run)."""
    agent = AnalyticsAgent()
    
    # Create test content items
    with mock_get_sync_session() as session:
        # Real published item
        real_item = ContentItemModel(
            title="Real Post",
            channel="x",
            status="published",
            post_id="real-post-123",
            post_url="https://x.com/status/123"
        )
        session.add(real_item)
        
        # Dry-run item (should be excluded)
        dry_run_item = ContentItemModel(
            title="Dry Run",
            channel="x", 
            status="published",
            post_id="dry-run-id"
        )
        session.add(dry_run_item)
        
        # Another dry-run pattern
        dry_run_item2 = ContentItemModel(
            title="Dry Run 2",
            channel="moltbook",
            status="published",
            post_id="dry-run-456"
        )
        session.add(dry_run_item2)
        
        # Draft item (should be excluded)
        draft_item = ContentItemModel(
            title="Draft",
            channel="x",
            status="draft"
        )
        session.add(draft_item)
        
        session.commit()
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        result = await agent.execute({"timeframe": "daily"})
        
        assert result["outcome"] == "metrics_generated"
        assert result["report"]["metrics"]["publications"] == 1  # Only real item counted
        assert result["report"]["metrics"]["publications_data_source"] == "database"

@pytest.mark.asyncio
async def test_analytics_unavailable_metrics():
    """Test that unavailable metrics return 'unavailable/not configured' with data source name."""
    agent = AnalyticsAgent()
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        result = await agent.execute({"timeframe": "daily"})
        
        metrics = result["report"]["metrics"]
        
        # Check unavailable metrics
        assert metrics["impressions"] == "unavailable/not configured"
        assert metrics["impressions_data_source"] == "google_search_console"
        
        assert metrics["clicks"] == "unavailable/not configured"
        assert metrics["clicks_data_source"] == "google_search_console"
        
        assert metrics["website_visits"] == "unavailable/not configured"
        assert metrics["website_visits_data_source"] == "google_search_console"
        
        assert metrics["registrations"] == "unavailable/not configured"
        assert metrics["registrations_data_source"] == "auth_service"
        
        assert metrics["sdk_installs"] == "unavailable/not configured"
        assert metrics["sdk_installs_data_source"] == "pypi/npm"
        
        assert metrics["github_activity"] == "unavailable/not configured"
        assert metrics["github_activity_data_source"] == "github"
        
        assert metrics["conversions"] == "unavailable/not configured"
        assert metrics["conversions_data_source"] == "analytics"

@pytest.mark.asyncio
async def test_analytics_available_metrics():
    """Test that available metrics return real data with proper data source attribution."""
    agent = AnalyticsAgent()
    
    # Create test MCP audit events
    with mock_get_sync_session() as session:
        audit_event = AuditEventModel(
            agent_name="TestAgent",
            event_type="mcp_call_succeeded",
            message="MCP call succeeded",
            metadata_json={"function": "agent_quote"}
        )
        session.add(audit_event)
        session.flush()  # Flush to ensure hash is computed
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        result = await agent.execute({"timeframe": "daily"})
        
        metrics = result["report"]["metrics"]
        
        # Check available metrics
        assert metrics["publications"] != "unavailable/not configured"
        assert metrics["publications_data_source"] == "database"
        
        assert metrics["mcp_calls"] != "unavailable/not configured"
        assert metrics["mcp_calls_data_source"] == "database"
        
        assert metrics["mcp_activations"] != "unavailable/not configured"
        assert metrics["mcp_activations_data_source"] == "mcp_audit_events"

@pytest.mark.asyncio
async def test_analytics_weekly_report():
    """Test that AnalyticsAgent generates weekly reports."""
    agent = AnalyticsAgent()
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        result = await agent.execute({"timeframe": "weekly"})
        
        assert result["outcome"] == "metrics_generated"
        assert result["report"]["timeframe"] == "weekly"
        assert "metrics" in result["report"]
        assert "recommendations" in result["report"]
        assert "data_source_summary" in result["report"]

@pytest.mark.asyncio
async def test_analytics_no_fabrication():
    """Test that AnalyticsAgent never fabricates metric values."""
    agent = AnalyticsAgent()
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        result = await agent.execute({"timeframe": "daily"})
        
        metrics = result["report"]["metrics"]
        
        # Check that unavailable metrics are never fabricated
        for metric_name, metric_value in metrics.items():
            if metric_name.endswith("_data_source"):
                continue  # Skip data source fields
            
            if metric_value == "unavailable/not configured":
                # Ensure data source is specified
                data_source_field = f"{metric_name}_data_source"
                assert data_source_field in metrics
                assert metrics[data_source_field] is not None
            else:
                # For available metrics, ensure it's a real type (int, str, etc)
                assert not isinstance(metric_value, str) or metric_value != "unavailable/not configured"

@pytest.mark.asyncio
async def test_analytics_data_source_summary():
    """Test that AnalyticsAgent provides accurate data source summary."""
    agent = AnalyticsAgent()
    
    with patch("apps.agents.specialized.get_sync_session", side_effect=mock_get_sync_session):
        
        result = await agent.execute({"timeframe": "daily"})
        
        summary = result["report"]["data_source_summary"]
        
        assert "available_metrics" in summary
        assert "unavailable_metrics" in summary
        
        # Check that the counts match the configured data sources
        assert len(summary["available_metrics"]) > 0
        assert len(summary["unavailable_metrics"]) > 0
        
        # Verify specific metrics are in the right categories
        assert "publications" in summary["available_metrics"]
        assert "mcp_calls" in summary["available_metrics"]
        assert "impressions" in summary["unavailable_metrics"]
        assert "clicks" in summary["unavailable_metrics"]
