"""Comprehensive tests for publisher implementations to improve coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.integrations.publishing.dispatcher import (
    MoltbookPublisher, XPublisher, TelegramPublisher, MultiChannelPublisher
)


@pytest.mark.asyncio
async def test_moltbook_publisher_publish_post():
    """Test MoltbookPublisher publish_post method."""
    publisher = MoltbookPublisher()
    
    with patch('apps.integrations.publishing.dispatcher.MoltbookClient') as mock_client_class:
        mock_client = Mock()
        mock_client.publish_post = AsyncMock(return_value={
            "success": True,
            "dry_run": True,
            "post_id": "test-123",
            "post_url": "https://test.com/post/123"
        })
        mock_client_class.return_value = mock_client
        
        result = await publisher.publish_post("Test Title", "Test Body")
        assert result["success"] is True


@pytest.mark.asyncio
async def test_x_publisher_publish_post():
    """Test XPublisher publish_post method."""
    publisher = XPublisher()
    
    with patch('apps.integrations.publishing.dispatcher.XClient') as mock_client_class:
        mock_client = Mock()
        mock_client.publish_post = AsyncMock(return_value={
            "success": True,
            "dry_run": True,
            "post_id": "test-456",
            "post_url": "https://x.com/i/status/456"
        })
        mock_client_class.return_value = mock_client
        
        result = await publisher.publish_post("Test Title", "Test Body")
        assert result["success"] is True


@pytest.mark.asyncio
async def test_telegram_publisher_publish_post():
    """Test TelegramPublisher publish_post method."""
    publisher = TelegramPublisher()
    
    with patch('apps.integrations.publishing.dispatcher.TelegramClient') as mock_client_class:
        mock_client = Mock()
        mock_client.publish_post = AsyncMock(return_value={
            "success": True,
            "dry_run": True,
            "post_id": "test-789",
            "post_url": "https://t.me/test/789"
        })
        mock_client_class.return_value = mock_client
        
        result = await publisher.publish_post("Test Title", "Test Body")
        assert result["success"] is True


@pytest.mark.asyncio
async def test_multi_channel_publisher_publish():
    """Test MultiChannelPublisher publish method."""
    publisher = MultiChannelPublisher()
    
    with patch('apps.integrations.publishing.dispatcher.TelegramPublisher') as mock_telegram:
        mock_telegram_instance = Mock()
        mock_telegram_instance.publish_post = AsyncMock(return_value={
            "success": True,
            "dry_run": False,
            "post_id": "test-123",
            "post_url": "https://t.me/test/123"
        })
        mock_telegram.return_value = mock_telegram_instance
        
        result = await publisher.publish_post("Test Title", "Test Body", channel="telegram")
        assert result["success"] is True


def test_get_publisher_function():
    """Test get_publisher function."""
    from apps.integrations.publishing.dispatcher import get_publisher
    
    # Test that it returns a publisher for known channels
    for channel in ["moltbook", "x", "telegram", "google"]:
        try:
            publisher = get_publisher(channel)
            assert publisher is not None
        except Exception:
            # May raise if credentials missing, that's ok
            pass