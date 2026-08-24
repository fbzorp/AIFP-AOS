"""Test for X client to improve coverage."""

import pytest
import httpx
from typing import Dict
from unittest.mock import Mock, patch, AsyncMock
from apps.integrations.x.client import XClient, is_transient_error


def test_is_transient_error_transport_error():
    """Test transient error detection for transport errors."""
    error = httpx.TransportError("Connection failed")
    assert is_transient_error(error) is True


def test_is_transient_error_connect_error():
    """Test transient error detection for connect errors."""
    error = httpx.ConnectError("Connection refused")
    assert is_transient_error(error) is True


def test_is_transient_error_read_timeout():
    """Test transient error detection for read timeout."""
    error = httpx.ReadTimeout("Read timeout")
    assert is_transient_error(error) is True


def test_is_transient_error_write_timeout():
    """Test transient error detection for write timeout."""
    error = httpx.WriteTimeout("Write timeout")
    assert is_transient_error(error) is True


def test_is_transient_error_pool_timeout():
    """Test transient error detection for pool timeout."""
    error = httpx.PoolTimeout("Pool timeout")
    assert is_transient_error(error) is True


def test_is_transient_error_5xx_status():
    """Test transient error detection for 5xx status codes."""
    mock_response = Mock()
    mock_response.status_code = 500
    error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)
    assert is_transient_error(error) is True


def test_is_transient_error_429_status():
    """Test transient error detection for 429 status code."""
    mock_response = Mock()
    mock_response.status_code = 429
    error = httpx.HTTPStatusError("Rate limit", request=Mock(), response=mock_response)
    assert is_transient_error(error) is True


def test_is_transient_error_4xx_status():
    """Test transient error detection for 4xx status codes (not 429)."""
    mock_response = Mock()
    mock_response.status_code = 404
    error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
    assert is_transient_error(error) is False


def test_is_transient_error_generic_exception():
    """Test transient error detection for generic exceptions."""
    error = ValueError("Some error")
    assert is_transient_error(error) is False


def test_x_client_init():
    """Test XClient initialization."""
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret",
        timeout=30
    )
    assert client._api_key == "test_key"
    assert client._api_secret == "test_secret"
    assert client._access_token == "test_token"
    assert client._access_token_secret == "test_token_secret"
    assert client._timeout == 30


def test_x_client_properties():
    """Test XClient property methods."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_API_KEY = "global_key"
        mock_settings.X_API_SECRET = "global_secret"
        mock_settings.X_ACCESS_TOKEN = "global_token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "global_token_secret"
        mock_settings.X_AUTOPUBLISH = True
        
        client = XClient()
        assert client.api_key == "global_key"
        assert client.api_secret == "global_secret"
        assert client.access_token == "global_token"
        assert client.access_token_secret == "global_token_secret"
        assert client.autopublish_enabled is True


def test_x_client_properties_with_local_override():
    """Test XClient properties with local override."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_API_KEY = "global_key"
        mock_settings.X_API_SECRET = "global_secret"
        mock_settings.X_ACCESS_TOKEN = "global_token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "global_token_secret"
        
        client = XClient(api_key="local_key")
        assert client.api_key == "local_key"
        assert client.api_secret == "global_secret"


def test_x_client_generate_oauth_signature():
    """Test OAuth signature generation."""
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )
    
    signature = client._generate_oauth_signature(
        "POST",
        "https://api.twitter.com/2/tweets",
        {"text": "test"}
    )
    
    assert isinstance(signature, str)
    assert len(signature) > 0


def test_x_client_generate_oauth_headers():
    """Test OAuth header generation."""
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )
    
    headers = client._generate_oauth_headers(
        "POST",
        "https://api.twitter.com/2/tweets",
        {"text": "test"}
    )
    
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("OAuth ")


@pytest.mark.asyncio
async def test_x_client_publish_post_dry_run():
    """Test publish_post when autopublish is disabled."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_AUTOPUBLISH = False

        client = XClient()
        result = await client.publish_post("Test tweet")

        assert result["success"] is False
        assert "error" in result
        assert result["post_id"] is None
        assert result["post_url"] is None


@pytest.mark.asyncio
async def test_x_client_publish_post_idempotent():
    """Test publish_post with existing post_id (idempotent)."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_AUTOPUBLISH = True

        client = XClient()
        result = await client.publish_post("Test tweet", post_id="123456")

        assert result["success"] is True
        assert result["post_id"] == "123456"
        assert result["post_url"] == "https://x.com/i/status/123456"


@pytest.mark.asyncio
async def test_x_client_publish_post_too_long():
    """Test publish_post with text exceeding 280 characters."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_AUTOPUBLISH = True
        
        client = XClient()
        long_text = "a" * 281
        
        with pytest.raises(ValueError, match="exceeds 280 characters"):
            await client.publish_post(long_text)


@pytest.mark.asyncio
async def test_x_client_publish_post_empty():
    """Test publish_post with empty text."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_AUTOPUBLISH = True
        
        client = XClient()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            await client.publish_post("   ")


@pytest.mark.asyncio
async def test_x_client_publish_post_missing_credentials():
    """Test publish_post with missing credentials."""
    with patch('apps.integrations.x.client.settings') as mock_settings:
        mock_settings.X_AUTOPUBLISH = True
        mock_settings.X_API_KEY = None
        mock_settings.X_API_SECRET = None
        mock_settings.X_ACCESS_TOKEN = None
        mock_settings.X_ACCESS_TOKEN_SECRET = None

        client = XClient()
        result = await client.publish_post("Test tweet")

        assert result["success"] is False
        assert "error" in result
        assert result["post_id"] is None


@pytest.mark.asyncio
async def test_x_client_close():
    """Test XClient close method."""
    client = XClient()
    await client.close()


@pytest.mark.asyncio
async def test_x_client_context_manager():
    """Test XClient context manager."""
    async with XClient() as client:
        assert client is not None