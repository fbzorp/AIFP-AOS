"""Tests for SEO page publisher to improve coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.integrations.publishing.seo_page_publisher import SeoPagePublisher


@pytest.mark.asyncio
async def test_seo_publisher_initialization():
    """Test SeoPagePublisher initialization."""
    publisher = SeoPagePublisher()
    assert publisher is not None


@pytest.mark.asyncio
async def test_seo_publisher_publish_post():
    """Test SeoPagePublisher publish_post method."""
    publisher = SeoPagePublisher()
    
    with patch('apps.integrations.publishing.seo_page_publisher.Path') as mock_path:
        mock_path.return_value.mkdir = Mock()
        mock_path.return_value.__truediv__ = Mock(return_value=Mock())
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__ = Mock()
            mock_open.return_value.__exit__ = Mock()
            
            result = await publisher.publish_post("Test Title", "Test Body")
            assert result["success"] is True


@pytest.mark.asyncio
async def test_seo_publisher_close():
    """Test SeoPagePublisher close method."""
    publisher = SeoPagePublisher()
    await publisher.close()
    # Should not raise any exception