"""Test for Telegram client to improve coverage."""

import pytest
import httpx
from typing import Dict
from unittest.mock import Mock, patch, AsyncMock
from apps.integrations.telegram.client import TelegramClient, is_transient_error


def test_telegram_is_transient_error_transport_error():
    """Test transient error detection for transport errors."""
    error = httpx.TransportError("Connection failed")
    assert is_transient_error(error) is True


def test_telegram_is_transient_error_connect_error():
    """Test transient error detection for connect errors."""
    error = httpx.ConnectError("Connection refused")
    assert is_transient_error(error) is True


def test_telegram_is_transient_error_5xx_status():
    """Test transient error detection for 5xx status codes."""
    mock_response = Mock()
    mock_response.status_code = 500
    error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)
    assert is_transient_error(error) is True


def test_telegram_is_transient_error_429_status():
    """Test transient error detection for 429 status code."""
    mock_response = Mock()
    mock_response.status_code = 429
    error = httpx.HTTPStatusError("Rate limit", request=Mock(), response=mock_response)
    assert is_transient_error(error) is True


def test_telegram_is_transient_error_4xx_status():
    """Test transient error detection for 4xx status codes (not 429)."""
    mock_response = Mock()
    mock_response.status_code = 404
    error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
    assert is_transient_error(error) is False


def test_telegram_client_init():
    """Test TelegramClient initialization."""
    client = TelegramClient(
        bot_token="test_token",
        chat_id="test_chat_id",
        timeout=30
    )
    assert client._bot_token == "test_token"
    assert client._chat_id == "test_chat_id"
    assert client._timeout == 30


def test_telegram_client_properties():
    """Test TelegramClient property methods."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "global_token"
        mock_settings.TELEGRAM_CHAT_ID = "global_chat_id"
        mock_settings.TELEGRAM_DEFAULT_CHANNEL = "@test_channel"
        mock_settings.TELEGRAM_AUTOPUBLISH = True
        
        client = TelegramClient()
        assert client.bot_token == "global_token"
        assert client.chat_id == "global_chat_id"
        assert client.default_channel == "@test_channel"
        assert client.autopublish_enabled is True


def test_telegram_client_properties_with_local_override():
    """Test TelegramClient properties with local override."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "global_token"
        mock_settings.TELEGRAM_CHAT_ID = "global_chat_id"
        
        client = TelegramClient(bot_token="local_token")
        assert client.bot_token == "local_token"
        assert client.chat_id == "global_chat_id"


@pytest.mark.asyncio
async def test_telegram_client_publish_post_dry_run():
    """Test publish_post when autopublish is disabled."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_AUTOPUBLISH = False

        client = TelegramClient()
        result = await client.publish_post("Test message")

        assert result["success"] is False
        assert "error" in result
        assert result["post_id"] is None
        assert result["post_url"] is None


@pytest.mark.asyncio
async def test_telegram_client_publish_post_idempotent():
    """Test publish_post with existing post_id (idempotent)."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_AUTOPUBLISH = True
        mock_settings.TELEGRAM_CHAT_ID = "test_chat"

        client = TelegramClient()
        result = await client.publish_post("Test message", post_id="123456")

        assert result["success"] is True
        assert result["post_id"] == "123456"
        assert result["post_url"] == "https://t.me/test_chat/123456"


@pytest.mark.asyncio
async def test_telegram_client_publish_post_empty():
    """Test publish_post with empty text."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_AUTOPUBLISH = True
        
        client = TelegramClient()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            await client.publish_post("   ")


@pytest.mark.asyncio
async def test_telegram_client_publish_post_missing_bot_token():
    """Test publish_post with missing bot token."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_AUTOPUBLISH = True
        mock_settings.TELEGRAM_BOT_TOKEN = None
        mock_settings.TELEGRAM_CHAT_ID = "test_chat"

        client = TelegramClient()
        result = await client.publish_post("Test message")

        assert result["success"] is False
        assert "error" in result
        assert result["post_id"] is None


@pytest.mark.asyncio
async def test_telegram_client_publish_post_missing_chat_id():
    """Test publish_post with missing chat_id."""
    with patch('apps.integrations.telegram.client.settings') as mock_settings:
        mock_settings.TELEGRAM_AUTOPUBLISH = True
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_CHAT_ID = None
        mock_settings.TELEGRAM_DEFAULT_CHANNEL = None

        client = TelegramClient()
        result = await client.publish_post("Test message")

        assert result["success"] is False
        assert "error" in result
        assert result["post_id"] is None


@pytest.mark.asyncio
async def test_telegram_client_close():
    """Test TelegramClient close method."""
    client = TelegramClient()
    await client.close()


@pytest.mark.asyncio
async def test_telegram_client_context_manager():
    """Test TelegramClient context manager."""
    async with TelegramClient() as client:
        assert client is not None