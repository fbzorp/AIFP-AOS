import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.models.base import Base, get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from apps.workers.tasks import publish_content

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
@patch("apps.integrations.moltbook.client.MoltbookClient.publish_post")
def test_publish_content_dry_run(mock_publish, mock_policy, mock_get_session):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    
    # Mock policy validation
    mock_policy.return_value.validate_approval.return_value = True
    
    # Mock publish result to avoid coroutine issues
    mock_publish.return_value = {
        "success": True,
        "dry_run": True,
        "post_id": "dry-run-id",
        "post_url": "https://www.moltbook.com/posts/dry-run-id"
    }
    
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
    with patch("apps.api.config.settings.MOLTBOOK_AUTOPUBLISH", False):
        publish_content(content.id, "appr-123", "hash-123")
    
    # Assertions
    assert content.status == "published"
    assert content.published_at is not None
    
    audit = session.query(AuditEventModel).filter(AuditEventModel.event_type == "content_published").first()
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
    
    with patch("apps.api.config.settings.MOLTBOOK_ALLOWED_SUBMOLTS", "general,aifintech"):
        with pytest.raises(ValueError, match="not in allowlist"):
            publish_content(content.id, "appr-123", "hash-123")
            
    assert content.status == "approved" # Should not change
    audit = session.query(AuditEventModel).filter(AuditEventModel.event_type == "publish_denied").first()
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
