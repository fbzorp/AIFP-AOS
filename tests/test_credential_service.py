"""Test for credential service to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from apps.core.credential.service import CredentialService


def test_get_x_credentials_sync_agent_specific():
    """Test getting X credentials with agent-specific credentials."""
    with patch('apps.core.credential.service.settings') as mock_settings:
        # Mock agent-specific credentials
        mock_settings.FOUNDER_CONTENT_X_API_KEY = "agent_key"
        mock_settings.FOUNDER_CONTENT_X_API_SECRET = "agent_secret"
        mock_settings.FOUNDER_CONTENT_X_ACCESS_TOKEN = "agent_token"
        mock_settings.FOUNDER_CONTENT_X_ACCESS_TOKEN_SECRET = "agent_token_secret"
        
        # Mock global credentials (should not be used)
        mock_settings.X_API_KEY = "global_key"
        mock_settings.X_API_SECRET = "global_secret"
        mock_settings.X_ACCESS_TOKEN = "global_token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "global_token_secret"
        
        result = CredentialService.get_x_credentials_sync("Founder Content")
        
        assert result["api_key"] == "agent_key"
        assert result["api_secret"] == "agent_secret"
        assert result["access_token"] == "agent_token"
        assert result["access_token_secret"] == "agent_token_secret"


def test_get_x_credentials_sync_global():
    """Test getting X credentials with global fallback."""
    with patch('apps.core.credential.service.settings') as mock_settings:
        # Mock no agent-specific credentials
        mock_settings.FOUNDER_CONTENT_X_API_KEY = None
        
        # Mock global credentials
        mock_settings.X_API_KEY = "global_key"
        mock_settings.X_API_SECRET = "global_secret"
        mock_settings.X_ACCESS_TOKEN = "global_token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "global_token_secret"
        
        result = CredentialService.get_x_credentials_sync("Founder Content")
        
        assert result["api_key"] == "global_key"
        assert result["api_secret"] == "global_secret"
        assert result["access_token"] == "global_token"
        assert result["access_token_secret"] == "global_token_secret"


def test_get_moltbook_credentials_sync_agent_specific():
    """Test getting Moltbook credentials with agent-specific credentials."""
    with patch('apps.core.credential.service.settings') as mock_settings:
        # Mock agent-specific credentials
        mock_settings.FOUNDER_CONTENT_MOLTBOOK_AGENT_API_KEY = "agent_key"
        mock_settings.FOUNDER_CONTENT_MOLTBOOK_APP_KEY = "agent_app_key"
        
        # Mock global credentials (should not be used)
        mock_settings.MOLTBOOK_AGENT_API_KEY = "global_key"
        mock_settings.MOLTBOOK_APP_KEY = "global_app_key"
        
        result = CredentialService.get_moltbook_credentials_sync("Founder Content")
        
        assert result["agent_api_key"] == "agent_key"
        assert result["app_key"] == "agent_app_key"


def test_get_moltbook_credentials_sync_global():
    """Test getting Moltbook credentials with global fallback."""
    with patch('apps.core.credential.service.settings') as mock_settings:
        # Mock no agent-specific credentials
        mock_settings.FOUNDER_CONTENT_MOLTBOOK_AGENT_API_KEY = None
        
        # Mock global credentials
        mock_settings.MOLTBOOK_AGENT_API_KEY = "global_key"
        mock_settings.MOLTBOOK_APP_KEY = "global_app_key"
        
        result = CredentialService.get_moltbook_credentials_sync("Founder Content")
        
        assert result["agent_api_key"] == "global_key"
        assert result["app_key"] == "global_app_key"


def test_get_telegram_credentials_sync_agent_specific():
    """Test getting Telegram credentials with agent-specific credentials."""
    with patch('apps.core.credential.service.settings') as mock_settings:
        # Mock agent-specific credentials
        mock_settings.FOUNDER_CONTENT_TELEGRAM_BOT_TOKEN = "agent_token"
        mock_settings.FOUNDER_CONTENT_TELEGRAM_CHAT_ID = "agent_chat_id"
        mock_settings.FOUNDER_CONTENT_TELEGRAM_DEFAULT_CHANNEL = "agent_channel"
        
        # Mock global credentials (should not be used)
        mock_settings.TELEGRAM_BOT_TOKEN = "global_token"
        mock_settings.TELEGRAM_CHAT_ID = "global_chat_id"
        mock_settings.TELEGRAM_DEFAULT_CHANNEL = "global_channel"
        
        result = CredentialService.get_telegram_credentials_sync("Founder Content")
        
        assert result["bot_token"] == "agent_token"
        assert result["chat_id"] == "agent_chat_id"
        assert result["default_channel"] == "agent_channel"


def test_get_telegram_credentials_sync_global():
    """Test getting Telegram credentials with global fallback."""
    with patch('apps.core.credential.service.settings') as mock_settings:
        # Mock no agent-specific credentials
        mock_settings.FOUNDER_CONTENT_TELEGRAM_BOT_TOKEN = None
        
        # Mock global credentials
        mock_settings.TELEGRAM_BOT_TOKEN = "global_token"
        mock_settings.TELEGRAM_CHAT_ID = "global_chat_id"
        mock_settings.TELEGRAM_DEFAULT_CHANNEL = "global_channel"
        
        result = CredentialService.get_telegram_credentials_sync("Founder Content")
        
        assert result["bot_token"] == "global_token"
        assert result["chat_id"] == "global_chat_id"
        assert result["default_channel"] == "global_channel"


@pytest.mark.asyncio
async def test_get_x_credentials_async():
    """Test async wrapper for X credentials."""
    with patch.object(CredentialService, 'get_x_credentials_sync') as mock_sync:
        mock_sync.return_value = {"api_key": "test_key"}
        
        result = await CredentialService.get_x_credentials("Test Agent")
        
        assert result["api_key"] == "test_key"
        mock_sync.assert_called_once_with("Test Agent")


@pytest.mark.asyncio
async def test_get_moltbook_credentials_async():
    """Test async wrapper for Moltbook credentials."""
    with patch.object(CredentialService, 'get_moltbook_credentials_sync') as mock_sync:
        mock_sync.return_value = {"agent_api_key": "test_key"}
        
        result = await CredentialService.get_moltbook_credentials("Test Agent")
        
        assert result["agent_api_key"] == "test_key"
        mock_sync.assert_called_once_with("Test Agent")


@pytest.mark.asyncio
async def test_get_telegram_credentials_async():
    """Test async wrapper for Telegram credentials."""
    with patch.object(CredentialService, 'get_telegram_credentials_sync') as mock_sync:
        mock_sync.return_value = {"bot_token": "test_token"}
        
        result = await CredentialService.get_telegram_credentials("Test Agent")
        
        assert result["bot_token"] == "test_token"
        mock_sync.assert_called_once_with("Test Agent")