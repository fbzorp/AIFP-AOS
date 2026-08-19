"""Tests for credential service sync methods to improve coverage."""

import pytest
from apps.core.credential.service import CredentialService


def test_credential_service_moltbook():
    """Test Moltbook credential retrieval."""
    result = CredentialService.get_moltbook_credentials_sync("test_agent")
    assert result is not None
    assert "agent_api_key" in result


def test_credential_service_x():
    """Test X credential retrieval."""
    result = CredentialService.get_x_credentials_sync("test_agent")
    assert result is not None
    assert "api_key" in result


def test_credential_service_telegram():
    """Test Telegram credential retrieval."""
    result = CredentialService.get_telegram_credentials_sync("test_agent")
    assert result is not None
    assert "bot_token" in result