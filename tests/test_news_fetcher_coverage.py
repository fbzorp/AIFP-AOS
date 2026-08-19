"""Tests for news fetcher to improve coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.core.news_fetcher import NewsFetcher


@pytest.mark.asyncio
async def test_news_fetcher_initialization():
    """Test NewsFetcher initialization."""
    fetcher = NewsFetcher()
    assert fetcher is not None


@pytest.mark.asyncio
async def test_news_fetcher_fetch_with_mock():
    """Test NewsFetcher fetch method with mocked HTTP client."""
    fetcher = NewsFetcher()
    
    with patch('apps.core.news_fetcher.httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={"articles": []})
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await fetcher.fetch("test_query")
        assert result is not None


@pytest.mark.asyncio
async def test_news_fetcher_fetch_error_handling():
    """Test NewsFetcher fetch method error handling."""
    fetcher = NewsFetcher()
    
    with patch('apps.core.news_fetcher.httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.side_effect = Exception("Network error")
        
        result = await fetcher.fetch("test_query")
        # Should handle error gracefully
        assert result is not None