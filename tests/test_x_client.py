"""Tests for X client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from apps.integrations.x.client import XClient


def test_x_client_initialization():
    """Test X client initialization."""
    client = XClient()
    assert client is not None


def test_x_client_with_credentials():
    """Test X client with credentials."""
    client = XClient(
        api_key="test-key",
        api_secret="test-secret",
        access_token="test-token",
        access_token_secret="test-token-secret"
    )
    assert client is not None


def test_x_client_has_publish_method():
    """Test that client has publish method."""
    client = XClient()
    assert hasattr(client, 'publish_post')


def test_x_client_has_search_method():
    """Test that client has search method."""
    client = XClient()
    assert hasattr(client, 'search')


def test_x_client_autopublish_property():
    """Test autopublish property."""
    client = XClient()
    assert hasattr(client, 'autopublish_enabled')


def test_x_client_api_key_property():
    """Test api_key property."""
    client = XClient()
    assert hasattr(client, 'api_key')


@pytest.mark.asyncio
async def test_x_search_disabled():
    """Test X search when disabled via settings."""
    with patch("apps.integrations.x.client.settings") as mock_settings:
        mock_settings.X_SEARCH_ENABLED = False
        
        client = XClient()
        result = await client.search("test query")
        
        assert result["success"] is True
        assert result["data"] == []
        assert result["meta"]["result_count"] == 0


@pytest.mark.asyncio
async def test_x_search_no_credentials():
    """Test X search when credentials not configured."""
    with patch("apps.integrations.x.client.settings") as mock_settings:
        mock_settings.X_SEARCH_ENABLED = True
        mock_settings.X_API_KEY = None
        
        client = XClient()
        result = await client.search("test query")
        
        assert result["success"] is True
        assert result["data"] == []
        assert result["meta"]["result_count"] == 0


@pytest.mark.asyncio
async def test_x_search_invalid_max_results():
    """Test X search with invalid max_results."""
    client = XClient()
    
    with pytest.raises(ValueError, match="max_results must be between 1 and 100"):
        await client.search("test query", max_results=0)
    
    with pytest.raises(ValueError, match="max_results must be between 1 and 100"):
        await client.search("test query", max_results=101)


@pytest.mark.asyncio
async def test_x_search_empty_query():
    """Test X search with empty query."""
    client = XClient()
    
    with pytest.raises(ValueError, match="Search query cannot be empty"):
        await client.search("")


@pytest.mark.asyncio
async def test_x_search_success():
    """Test successful X search."""
    mock_response_data = {
        "data": [
            {
                "id": "1234567890",
                "text": "Test tweet about autonomous publishing",
                "author_id": "987654321",
                "created_at": "2024-01-01T00:00:00Z",
                "public_metrics": {"like_count": 10, "retweet_count": 5},
                "lang": "en"
            }
        ],
        "meta": {"result_count": 1, "next_token": "next-token"}
    }
    
    with patch("apps.integrations.x.client.settings") as mock_settings:
        mock_settings.X_SEARCH_ENABLED = True
        mock_settings.X_API_KEY = "test-key"
        mock_settings.X_API_SECRET = "test-secret"
        mock_settings.X_ACCESS_TOKEN = "test-token"
        mock_settings.X_ACCESS_TOKEN_SECRET = "test-token-secret"
        
        client = XClient()
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.http, 'get', AsyncMock(return_value=mock_response)):
            result = await client.search("autonomous publishing", max_results=10)
            
            assert result["success"] is True
            assert len(result["data"]) == 1
            assert result["data"][0]["id"] == "1234567890"
            assert result["meta"]["result_count"] == 1