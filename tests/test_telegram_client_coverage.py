"""Tests for Telegram client to improve coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.integrations.telegram.client import TelegramClient


@pytest.mark.asyncio
async def test_telegram_client_initialization():
    """Test TelegramClient initialization."""
    client = TelegramClient(
        bot_token="test_token",
        chat_id="test_chat_id"
    )
    assert client is not None


@pytest.mark.asyncio
async def test_telegram_client_publish_post():
    """Test TelegramClient publish_post method."""
    client = TelegramClient(
        bot_token="test_token",
        chat_id="test_chat_id"
    )
    
    with patch('apps.integrations.telegram.client.httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={"ok": True, "result": {"message_id": 123}})
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await client.publish_post(text="Test message")
        assert result["success"] is True


@pytest.mark.asyncio
async def test_telegram_client_close():
    """Test TelegramClient close method."""
    client = TelegramClient(
        bot_token="test_token",
        chat_id="test_chat_id"
    )
    await client.close()
    # Should not raise any exception