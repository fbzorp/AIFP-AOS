"""Tests for credential service to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from apps.core.credential.service import CredentialService


def test_get_moltbook_credentials_sync():
    """Test sync credential retrieval for Moltbook."""
    result = CredentialService.get_moltbook_credentials_sync("test_agent")
    assert result is not None
    assert "agent_api_key" in result


def test_get_x_credentials_sync():
    """Test sync credential retrieval for X."""
    result = CredentialService.get_x_credentials_sync("test_agent")
    assert result is not None
    assert "api_key" in result


def test_get_telegram_credentials_sync():
    """Test sync credential retrieval for Telegram."""
    result = CredentialService.get_telegram_credentials_sync("test_agent")
    assert result is not None
    assert "bot_token" in result


@pytest.mark.asyncio
async def test_get_moltbook_credentials_async():
    """Test async credential retrieval for Moltbook."""
    result = await CredentialService.get_moltbook_credentials("test_agent")
    assert result is not None
    assert "agent_api_key" in result


@pytest.mark.asyncio
async def test_get_x_credentials_async():
    """Test async credential retrieval for X."""
    result = await CredentialService.get_x_credentials("test_agent")
    assert result is not None
    assert "api_key" in result


@pytest.mark.asyncio
async def test_get_telegram_credentials_async():
    """Test async credential retrieval for Telegram."""
    result = await CredentialService.get_telegram_credentials("test_agent")
    assert result is not None
    assert "bot_token" in result