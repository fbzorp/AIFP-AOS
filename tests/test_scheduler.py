"""Tests for scheduled tasks."""

import pytest
from unittest.mock import patch, MagicMock
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    scheduled_seo_sitemap_update
)


def test_scheduled_autonomous_publisher_no_content():
    """Test autonomous publisher when no approved content exists."""
    with patch('apps.workers.scheduler.get_sync_session') as mock_session:
        mock_session.return_value.__enter__.return_value.execute.return_value.scalars.return_value.all.return_value = []
        
        scheduled_autonomous_publisher()
        
        # Should complete without error when no content exists
        assert True


def test_scheduled_seo_sitemap_update():
    """Test SEO sitemap update task."""
    with patch('apps.integrations.publishing.seo_page_publisher.SeoPagePublisher') as mock_publisher_class:
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher
        
        with patch('apps.workers.scheduler.get_sync_session') as mock_session:
            mock_session.return_value.__enter__.return_value.execute.return_value.scalars.return_value.all.return_value = []
            
            scheduled_seo_sitemap_update()
            
            # Verify publisher was initialized and sitemap updated
            mock_publisher._ensure_initialized.assert_called_once()
            mock_publisher._update_sitemap_and_robots.assert_called_once()


def test_scheduled_seo_content_generator():
    """Test SEO content generator task - basic smoke test."""
    # This test just verifies the function can be imported and has the right signature
    # Full integration testing would require database setup
    assert callable(scheduled_seo_content_generator)
