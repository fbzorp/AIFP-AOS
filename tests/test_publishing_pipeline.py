"""
Tests for the new publishing pipeline (Phase 1 remediation).
Tests dry-run integrity, channel-agnostic dispatch, and X/Telegram client structure.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.models.base import Base, get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.workers.tasks import _perform_publish_logic
from apps.integrations.publishing import get_publisher

# Setup in-memory SQLite for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create and clean up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_session():
    """Create a test session."""
    return TestingSessionLocal()


class TestDryRunIntegrity:
    """Tests for dry-run integrity in publishing logic."""
    
    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    @patch("apps.integrations.publishing.get_publisher")
    def test_dry_run_sets_correct_status(self, mock_get_publisher, mock_policy, mock_get_session):
        """Test that dry_run sets status='dry_run' and does NOT stamp fake post_id."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_policy.return_value.validate_approval.return_value = True
        
        # Mock publisher that returns dry_run=True
        mock_publisher = AsyncMock()
        mock_publisher.publish_post = AsyncMock(return_value={
            "success": True,
            "dry_run": True,
            "post_id": "dry-run-id",
            "post_url": "https://example.com/dry-run"
        })
        mock_publisher.__aenter__ = AsyncMock(return_value=mock_publisher)
        mock_publisher.__aexit__ = AsyncMock()
        mock_get_publisher.return_value = mock_publisher
        
        # Create approved content
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            channel="moltbook",
            status="approved"
        )
        session.add(content)
        session.commit()
        
        result = asyncio.run(_perform_publish_logic(session, "content-1", "appr-123", "hash-123"))
        
        # Verify dry_run status
        assert result["status"] == "dry_run"
        assert result["dry_run"] is True
        
        # Verify content was NOT stamped with fake values
        updated_content = session.query(ContentItemModel).filter(ContentItemModel.id == "content-1").first()
        assert updated_content.status == "dry_run"
        assert updated_content.post_id is None
        assert updated_content.post_url is None
        assert updated_content.published_at is None
    
    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    @patch("apps.integrations.publishing.get_publisher")
    def test_real_publish_stamps_real_values(self, mock_get_publisher, mock_policy, mock_get_session):
        """Test that real publish sets status='published' and stamps real post_id."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_policy.return_value.validate_approval.return_value = True
        
        # Mock publisher that returns dry_run=False
        mock_publisher = AsyncMock()
        mock_publisher.publish_post = AsyncMock(return_value={
            "success": True,
            "dry_run": False,
            "post_id": "real-post-123",
            "post_url": "https://example.com/posts/real-post-123"
        })
        mock_publisher.__aenter__ = AsyncMock(return_value=mock_publisher)
        mock_publisher.__aexit__ = AsyncMock()
        mock_get_publisher.return_value = mock_publisher
        
        # Create approved content
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            channel="moltbook",
            status="approved"
        )
        session.add(content)
        session.commit()
        
        result = asyncio.run(_perform_publish_logic(session, "content-1", "appr-123", "hash-123"))
        
        # Verify published status
        assert result["status"] == "published"
        assert result["dry_run"] is False
        assert result["post_id"] == "real-post-123"
        
        # Verify content was stamped with real values
        updated_content = session.query(ContentItemModel).filter(ContentItemModel.id == "content-1").first()
        assert updated_content.status == "published"
        assert updated_content.post_id == "real-post-123"
        assert updated_content.post_url == "https://example.com/posts/real-post-123"
        assert updated_content.published_at is not None


class TestPublisherDispatcher:
    """Tests for channel-agnostic publisher dispatcher."""
    
    def test_dispatcher_routes_moltbook(self):
        """Test that 'moltbook' channel routes to MoltbookPublisher."""
        from apps.integrations.publishing.dispatcher import MoltbookPublisher
        
        publisher = get_publisher("moltbook")
        assert isinstance(publisher, MoltbookPublisher)
    
    def test_dispatcher_routes_x(self):
        """Test that 'x' channel routes to XPublisher."""
        from apps.integrations.publishing.dispatcher import XPublisher
        
        publisher = get_publisher("x")
        assert isinstance(publisher, XPublisher)
    
    def test_dispatcher_routes_twitter(self):
        """Test that 'twitter' channel routes to XPublisher."""
        from apps.integrations.publishing.dispatcher import XPublisher
        
        publisher = get_publisher("twitter")
        assert isinstance(publisher, XPublisher)
    
    def test_dispatcher_routes_telegram(self):
        """Test that 'telegram' channel routes to TelegramPublisher."""
        from apps.integrations.publishing.dispatcher import TelegramPublisher
        
        publisher = get_publisher("telegram")
        assert isinstance(publisher, TelegramPublisher)
    
    def test_dispatcher_raises_on_unsupported_channel(self):
        """Test that unsupported channels raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported channel"):
            get_publisher("unsupported_channel")


class TestXClient:
    """Tests for X/Twitter client structure."""
    
    @patch("apps.integrations.x.client.settings")
    def test_x_client_honors_autopublish_gate(self, mock_settings):
        """Test that X client returns dry_run when autopublish is disabled."""
        from apps.integrations.x.client import XClient
        
        mock_settings.X_AUTOPUBLISH = False
        mock_settings.X_API_KEY = "test_key"
        mock_settings.X_API_SECRET = "test_secret"
        mock_settings.X_ACCESS_TOKEN = "test_token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "test_secret"
        
        client = XClient()
        result = asyncio.run(client.publish_post("Test tweet"))
        
        assert result["dry_run"] is True
        assert result["post_id"] is None
        assert result["post_url"] is None
    
    @patch("apps.integrations.x.client.settings")
    def test_x_client_idempotency_skip_existing_post_id(self, mock_settings):
        """Test that X client skips publishing if post_id already exists."""
        from apps.integrations.x.client import XClient
        
        mock_settings.X_AUTOPUBLISH = True
        mock_settings.X_API_KEY = "test_key"
        mock_settings.X_API_SECRET = "test_secret"
        mock_settings.X_ACCESS_TOKEN = "test_token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "test_secret"
        
        client = XClient()
        result = asyncio.run(client.publish_post("Test tweet", post_id="existing-123"))
        
        assert result["dry_run"] is False
        assert result["post_id"] == "existing-123"
        assert result["post_url"] == "https://x.com/i/status/existing-123"


class TestTelegramClient:
    """Tests for Telegram client structure."""
    
    @patch("apps.integrations.telegram.client.settings")
    def test_telegram_client_honors_autopublish_gate(self, mock_settings):
        """Test that Telegram client returns dry_run when autopublish is disabled."""
        from apps.integrations.telegram.client import TelegramClient
        
        mock_settings.TELEGRAM_AUTOPUBLISH = False
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_CHAT_ID = "test_chat"
        
        client = TelegramClient()
        result = asyncio.run(client.publish_post("Test message"))
        
        assert result["dry_run"] is True
        assert result["post_id"] is None
        assert result["post_url"] is None
    
    @patch("apps.integrations.telegram.client.settings")
    def test_telegram_client_idempotency_skip_existing_post_id(self, mock_settings):
        """Test that Telegram client skips publishing if post_id already exists."""
        from apps.integrations.telegram.client import TelegramClient
        
        mock_settings.TELEGRAM_AUTOPUBLISH = True
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_CHAT_ID = "test_channel"
        
        client = TelegramClient()
        result = asyncio.run(client.publish_post("Test message", post_id="existing-456"))
        
        assert result["dry_run"] is False
        assert result["post_id"] == "existing-456"
        assert result["post_url"] == "https://t.me/test_channel/existing-456"
