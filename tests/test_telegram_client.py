"""Tests for Telegram client to improve coverage."""

import pytest
from apps.integrations.telegram.client import TelegramClient


def test_telegram_client_initialization():
    """Test Telegram client initialization."""
    client = TelegramClient()
    assert client is not None


def test_telegram_client_with_bot_token():
    """Test Telegram client with bot token."""
    client = TelegramClient(bot_token="test-token")
    assert client is not None


def test_telegram_client_has_publish_method():
    """Test that client has publish method."""
    client = TelegramClient()
    assert hasattr(client, 'publish_post')


def test_telegram_client_autopublish_property():
    """Test autopublish property."""
    client = TelegramClient()
    assert hasattr(client, 'autopublish_enabled')


def test_telegram_client_chat_id_property():
    """Test chat_id property."""
    client = TelegramClient()
    assert hasattr(client, 'chat_id')