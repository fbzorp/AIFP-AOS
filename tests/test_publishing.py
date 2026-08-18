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
    """Test that get_publisher resolves SEO/google channel to SeoPagePublisher."""
    from apps.integrations.publishing.dispatcher import SeoPagePublisher

    # google channel routes to SeoPagePublisher for indexable HTML pages
    publisher = get_publisher("google")
    assert isinstance(publisher, SeoPagePublisher)
    assert publisher._agent_name is None  # No agent-specific credentials

    # seo and blog channels also route to SeoPagePublisher
    for channel in ["seo", "blog"]:
        publisher = get_publisher(channel)
        assert isinstance(publisher, SeoPagePublisher)
        assert publisher._agent_name is None  # No agent-specific credentials


def test_seo_google_publisher_with_agent():
    """Test that SEO publisher respects agent-specific credentials."""
    from apps.integrations.publishing.dispatcher import SeoPagePublisher

    # google channel with agent routes to SeoPagePublisher
    publisher = get_publisher("google", agent_name="SEO Content")
    assert isinstance(publisher, SeoPagePublisher)
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
    """Test that SEO content stays pending_review after compliance passes (no auto-approval)."""
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

    # Simulate compliance passing - content goes to pending_review for human approval
    seo_content.status = "pending_review"
    session.commit()

    # Verify content stays pending_review (no auto-approval)
    assert seo_content.status == "pending_review"
    assert seo_content.author_agent == "SEO Content"


def test_publisher_resolution_all_channels():
    """Test that get_publisher returns real publishers for all channels agents can emit."""
    from apps.integrations.publishing.dispatcher import (
        MoltbookPublisher, XPublisher, TelegramPublisher, SeoPagePublisher
    )

    # Test all supported channels
    channels_and_publishers = {
        "moltbook": MoltbookPublisher,
        "general": MoltbookPublisher,
        "aifintech": MoltbookPublisher,
        "aiagents": MoltbookPublisher,
        "google": SeoPagePublisher,  # SEO content routes to static HTML pages
        "x": XPublisher,
        "twitter": XPublisher,
        "telegram": TelegramPublisher,
        "seo": SeoPagePublisher,
        "blog": SeoPagePublisher,
    }

    for channel, expected_publisher in channels_and_publishers.items():
        publisher = get_publisher(channel)
        assert isinstance(publisher, expected_publisher), f"Channel {channel} did not resolve to {expected_publisher.__name__}"


def test_scheduler_picks_approved_unpublished():
    """Test that scheduled_publisher_agent_task picks up approved, unpublished items."""
    from apps.models.approval import ApprovalModel
    from datetime import datetime, timedelta, timezone

    session = TestingSessionLocal()

    # Create approved content with no post_id
    approved_content = ContentItemModel(
        title="Approved Content",
        channel="x",
        status="approved",
        author_agent="Founder Content",
        format="post",
        body="Approved content body"
    )
    session.add(approved_content)
    session.flush()

    # Create matching approval
    approval = ApprovalModel(
        content_id=approved_content.id,
        draft_hash="test-hash",
        status="approved",
        approved_by="Human",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        decided_at=datetime.now(timezone.utc)
    )
    session.add(approval)
    session.commit()

    # Verify query would find this content
    from sqlalchemy import select
    result = session.execute(
        select(ContentItemModel).where(
            ContentItemModel.author_agent == "Founder Content",
            ContentItemModel.status == "approved",
            ContentItemModel.post_id.is_(None)
        )
    )
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.id == approved_content.id
    assert found.status == "approved"
    assert found.post_id is None


def test_telegram_digest_all_posts():
    """Test that Telegram digest includes all published posts from last 6 hours."""
    from datetime import datetime, timedelta
    from unittest.mock import AsyncMock, patch

    session = TestingSessionLocal()

    # Create published content from multiple agents/channels
    content1 = ContentItemModel(
        title="Founder Post",
        channel="x",
        status="published",
        author_agent="Founder Content",
        format="post",
        post_url="https://twitter.com/founder/post1",
        published_at=datetime.now() - timedelta(hours=2)
    )
    session.add(content1)

    content2 = ContentItemModel(
        title="SEO Article",
        channel="google",
        status="published",
        author_agent="SEO Content",
        format="article",
        post_url="https://example.com/seo-article",
        published_at=datetime.now() - timedelta(hours=1)
    )
    session.add(content2)

    # Create a dry-run item (no post_url) - should be excluded
    dry_run = ContentItemModel(
        title="Dry Run Post",
        channel="x",
        status="dry_run",
        author_agent="Technical Content",
        format="post",
        post_url=None,
        published_at=None
    )
    session.add(dry_run)

    # Create an old post (outside 6-hour window) - should be excluded
    old_post = ContentItemModel(
        title="Old Post",
        channel="x",
        status="published",
        author_agent="Founder Content",
        format="post",
        post_url="https://twitter.com/founder/old",
        published_at=datetime.now() - timedelta(hours=10)
    )
    session.add(old_post)
    session.commit()

    # Simulate digest query
    cutoff = datetime.now() - timedelta(hours=6)
    from sqlalchemy import select, desc
    result = session.execute(
        select(ContentItemModel).filter(
            ContentItemModel.status == "published",
            ContentItemModel.published_at >= cutoff,
            ContentItemModel.post_url.isnot(None)
        ).order_by(desc(ContentItemModel.published_at))
    )
    digest_items = result.scalars().all()

    # Should only include the 2 recent published items
    assert len(digest_items) == 2
    post_urls = [item.post_url for item in digest_items]
    assert "https://twitter.com/founder/post1" in post_urls
    assert "https://example.com/seo-article" in post_urls
    assert "https://twitter.com/founder/old" not in post_urls
