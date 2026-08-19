"""Tests for X client to improve coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.integrations.x.client import XClient


@pytest.mark.asyncio
async def test_x_client_initialization():
    """Test XClient initialization."""
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )
    assert client is not None


@pytest.mark.asyncio
async def test_x_client_publish_post():
    """Test XClient publish_post method."""
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )
    
    with patch('apps.integrations.x.client.httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={"data": {"id": "123"}})
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await client.publish_post(text="Test tweet")
        assert result["success"] is True


@pytest.mark.asyncio
async def test_x_client_close():
    """Test XClient close method."""
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )
    await client.close()
    # Should not raise any exception