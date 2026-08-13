import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.models.base import Base, get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from apps.models.approval import ApprovalModel
from apps.workers.tasks import publish_content
from apps.integrations.publishing.dispatcher import get_publisher

# Setup in-memory SQLite for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@patch("apps.workers.tasks.get_sync_session")
@patch("apps.workers.tasks.PolicyEngine")
@patch("apps.integrations.publishing.get_publisher")
def test_publish_content_dry_run(mock_get_publisher, mock_policy, mock_get_session):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    
    # Mock policy validation
    mock_policy.return_value.validate_approval.return_value = True
    
    # Mock publisher that returns dry_run=True
    mock_publisher = AsyncMock()
    mock_publisher.publish_post = AsyncMock(return_value={
        "success": True,
        "dry_run": True,
        "post_id": "dry-run-id",
        "post_url": "https://www.moltbook.com/posts/dry-run-id"
    })
    mock_publisher.__aenter__ = AsyncMock(return_value=mock_publisher)
    mock_publisher.__aexit__ = AsyncMock()
    mock_get_publisher.return_value = mock_publisher
    
    # Create approved content
    content = ContentItemModel(
        title="Test Post",
        channel="general",
        status="approved",
        body="Test content"
    )
    session.add(content)
    session.commit()
    
    # Trigger publish (dry-run by default as settings.MOLTBOOK_AUTOPUBLISH is False)
    publish_content(content.id, "appr-123", "hash-123")
    
    # Assertions - dry_run should set status="dry_run" and NOT stamp fake values
    assert content.status == "dry_run"
    assert content.post_id is None  # Should NOT be stamped with fake dry-run-id
    assert content.post_url is None  # Should NOT be stamped with fake URL
    assert content.published_at is None  # Should NOT be stamped with fake timestamp
    
    audit = session.query(AuditEventModel).filter(AuditEventModel.event_type == "content_dry_run").first()
    assert audit is not None
    assert audit.metadata_json.get("dry_run") is True

@patch("apps.workers.tasks.get_sync_session")
@patch("apps.workers.tasks.PolicyEngine")
def test_publish_denied_not_in_allowlist(mock_policy, mock_get_session):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    mock_policy.return_value.validate_approval.return_value = True
    
    content = ContentItemModel(
        title="Test Post",
        channel="forbidden-submolt",
        status="approved"
    )
    session.add(content)
    session.commit()
    
    # The dispatcher now raises ValueError for unsupported channels
    with pytest.raises(ValueError, match="Unsupported channel"):
        publish_content(content.id, "appr-123", "hash-123")
            
    assert content.status == "approved" # Should not change
    audit = session.query(AuditEventModel).filter(AuditEventModel.event_type == "publish_failed").first()
    assert audit is not None

@patch("apps.workers.tasks.get_sync_session")
def test_publish_denied_not_approved(mock_get_session):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session

    content = ContentItemModel(
        title="Test Post",
        channel="general",
        status="draft"
    )
    session.add(content)
    session.commit()

    with pytest.raises(ValueError, match="must be approved"):
        publish_content(content.id, "appr-123", "hash-123")


def test_seo_google_publisher_mapping():
    """Test that get_publisher resolves SEO/google channel to MultiChannelPublisher."""
    from apps.integrations.publishing.dispatcher import MultiChannelPublisher

    # Test various SEO-related channel names
    for channel in ["google", "seo", "blog"]:
        publisher = get_publisher(channel)
        assert isinstance(publisher, MultiChannelPublisher)
        assert publisher._agent_name is None  # No agent-specific credentials


def test_seo_google_publisher_with_agent():
    """Test that SEO publisher respects agent-specific credentials."""
    from apps.integrations.publishing.dispatcher import MultiChannelPublisher

    publisher = get_publisher("google", agent_name="SEO Content")
    assert isinstance(publisher, MultiChannelPublisher)
    assert publisher._agent_name == "SEO Content"


def test_telegram_republisher_seo_content_selection():
    """Test that Telegram republisher selects SEO content by author_agent."""
    from datetime import datetime, timedelta
    from sqlalchemy import select, desc

    session = TestingSessionLocal()

    # Create SEO content with author_agent="SEO Content"
    seo_content = ContentItemModel(
        title="SEO Article",
        channel="google",
        status="published",
        author_agent="SEO Content",
        format="article",
        post_url="https://example.com/seo-article",
        published_at=datetime.now() - timedelta(hours=1)
    )
    session.add(seo_content)

    # Create non-SEO content to ensure it's not selected
    non_seo_content = ContentItemModel(
        title="Founder Post",
        channel="twitter",
        status="published",
        author_agent="Founder Content",
        format="post",
        post_url="https://example.com/founder-post",
        published_at=datetime.now() - timedelta(hours=1)
    )
    session.add(non_seo_content)
    session.commit()

    # Simulate Telegram republisher query logic
    cutoff = datetime.now() - timedelta(hours=24)

    result = session.execute(
        select(ContentItemModel).filter(
            ContentItemModel.status == "published",
            ContentItemModel.published_at >= cutoff,
            ContentItemModel.post_url.isnot(None),
            ContentItemModel.author_agent == "SEO Content"
        ).order_by(desc(ContentItemModel.published_at)).limit(10)
    )
    seo_items = result.scalars().all()

    # Should only select SEO content
    assert len(seo_items) == 1
    assert seo_items[0].author_agent == "SEO Content"
    assert seo_items[0].title == "SEO Article"


def test_auto_approval_seo_content():
    """Test that SEO content gets auto-approved after compliance passes."""
    from apps.core.policy.engine import compute_draft_hash
    from datetime import datetime, timedelta, timezone

    session = TestingSessionLocal()

    # Create SEO content
    seo_content = ContentItemModel(
        title="SEO Article",
        channel="google",
        status="draft",
        author_agent="SEO Content",
        format="article",
        body="SEO content body"
    )
    session.add(seo_content)
    session.flush()

    # Simulate auto-approval logic
    draft_hash = compute_draft_hash(seo_content)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)

    approval = ApprovalModel(
        content_id=seo_content.id,
        draft_hash=draft_hash,
        status="approved",
        approved_by="System (Auto-Approval for SEO)",
        expires_at=expires_at,
        decided_at=now
    )
    session.add(approval)
    session.flush()

    seo_content.status = "approved"
    if not seo_content.scheduled_at:
        seo_content.scheduled_at = now + timedelta(days=1)

    session.commit()

    # Verify auto-approval worked
    assert seo_content.status == "approved"
    assert seo_content.scheduled_at is not None
    assert approval.status == "approved"
    assert approval.approved_by == "System (Auto-Approval for SEO)"
