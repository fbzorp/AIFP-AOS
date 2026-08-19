"""Test for publishing dispatcher to improve coverage."""

import pytest
from typing import Dict
from unittest.mock import Mock, AsyncMock, patch
from apps.integrations.publishing.dispatcher import (
    PublisherBase,
    MoltbookPublisher,
    XPublisher,
    TelegramPublisher,
    MultiChannelPublisher,
    get_publisher
)


def test_get_publisher_moltbook():
    """Test getting Moltbook publisher."""
    publisher = get_publisher("moltbook")
    assert isinstance(publisher, MoltbookPublisher)


def test_get_publisher_general():
    """Test getting general publisher (maps to Moltbook)."""
    publisher = get_publisher("general")
    assert isinstance(publisher, MoltbookPublisher)


def test_get_publisher_aifintech():
    """Test getting aifintech publisher (maps to Moltbook)."""
    publisher = get_publisher("aifintech")
    assert isinstance(publisher, MoltbookPublisher)


def test_get_publisher_aiagents():
    """Test getting aiagents publisher (maps to Moltbook)."""
    publisher = get_publisher("aiagents")
    assert isinstance(publisher, MoltbookPublisher)


def test_get_publisher_x():
    """Test getting X publisher."""
    publisher = get_publisher("x")
    assert isinstance(publisher, XPublisher)


def test_get_publisher_twitter():
    """Test getting Twitter publisher (maps to X)."""
    publisher = get_publisher("twitter")
    assert isinstance(publisher, XPublisher)


def test_get_publisher_telegram():
    """Test getting Telegram publisher."""
    publisher = get_publisher("telegram")
    assert isinstance(publisher, TelegramPublisher)


def test_get_publisher_seo():
    """Test getting SEO publisher."""
    publisher = get_publisher("seo")
    assert publisher is not None


def test_get_publisher_blog():
    """Test getting blog publisher (maps to SEO)."""
    publisher = get_publisher("blog")
    assert publisher is not None


def test_get_publisher_invalid():
    """Test getting publisher for invalid channel raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported channel"):
        get_publisher("invalid_channel")


def test_get_publisher_with_agent_name():
    """Test getting publisher with agent name."""
    publisher = get_publisher("moltbook", "Test Agent")
    assert isinstance(publisher, MoltbookPublisher)
    assert publisher._agent_name == "Test Agent"


def test_moltbook_publisher_init():
    """Test MoltbookPublisher initialization."""
    publisher = MoltbookPublisher("Test Agent")
    assert publisher._agent_name == "Test Agent"
    assert publisher._client is None
    assert publisher._initialized is False


def test_x_publisher_init():
    """Test XPublisher initialization."""
    publisher = XPublisher("Test Agent")
    assert publisher._agent_name == "Test Agent"
    assert publisher._client is None
    assert publisher._initialized is False


def test_telegram_publisher_init():
    """Test TelegramPublisher initialization."""
    publisher = TelegramPublisher("Test Agent")
    assert publisher._agent_name == "Test Agent"
    assert publisher._client is None
    assert publisher._initialized is False


def test_multi_channel_publisher_init():
    """Test MultiChannelPublisher initialization."""
    publisher = MultiChannelPublisher("Test Agent")
    assert publisher._agent_name == "Test Agent"
    assert publisher._publishers == {}
    assert publisher._initialized is False


@pytest.mark.asyncio
async def test_multi_channel_publisher_no_publishers():
    """Test MultiChannelPublisher with no available publishers."""
    with patch('apps.integrations.publishing.dispatcher.get_publisher') as mock_get:
        mock_get.side_effect = Exception("No credentials")
        
        publisher = MultiChannelPublisher("Test Agent")
        result = await publisher.publish_post("Test Title", "Test Body")
        
        assert result["success"] is False
        assert result["error"] == "No publishers available"


@pytest.mark.asyncio
async def test_publisher_base_context_manager():
    """Test PublisherBase context manager methods."""
    class TestPublisher(PublisherBase):
        async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
            return {"success": True}
        
        async def close(self):
            pass
    
    publisher = TestPublisher()
    
    # Test __aenter__
    result = await publisher.__aenter__()
    assert result is publisher
    
    # Test __aexit__
    await publisher.__aexit__(None, None, None)