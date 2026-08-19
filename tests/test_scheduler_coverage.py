"""Tests for scheduler module to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    scheduled_seo_sitemap_update,
    setup_scheduled_tasks
)


def test_scheduled_autonomous_publisher_no_content():
    """Test scheduled_autonomous_publisher when no content to publish."""
    with patch('apps.workers.scheduler.get_sync_session') as mock_session:
        mock_db = Mock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_session.return_value.__enter__.return_value = mock_db
        
        scheduled_autonomous_publisher()
        # Should complete without error


def test_scheduled_telegram_republisher_no_agent():
    """Test scheduled_telegram_republisher when agent not found."""
    with patch('apps.workers.scheduler.get_agent') as mock_get_agent:
        mock_get_agent.return_value = None
        
        scheduled_telegram_republisher()
        # Should complete without error


def test_scheduled_telegram_digest_no_agent():
    """Test scheduled_telegram_digest when agent not found."""
    with patch('apps.workers.scheduler.get_agent') as mock_get_agent:
        mock_get_agent.return_value = None
        
        scheduled_telegram_digest()
        # Should complete without error


def test_scheduled_seo_content_generator():
    """Test scheduled_seo_content_generator."""
    with patch('apps.workers.scheduler.get_sync_session') as mock_session:
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_session.return_value.__enter__.return_value = mock_db
        
        with patch('apps.workers.scheduler.run_agent_task') as mock_task:
            mock_task.send = Mock()
            
            scheduled_seo_content_generator()
            # Should complete without error


def test_scheduled_seo_sitemap_update():
    """Test scheduled_seo_sitemap_update."""
    with patch('apps.workers.scheduler.SeoPagePublisher') as mock_publisher:
        mock_instance = Mock()
        mock_instance._ensure_initialized = Mock()
        mock_instance._update_sitemap_and_robots = Mock()
        mock_publisher.return_value = mock_instance
        
        with patch('apps.workers.scheduler.get_sync_session') as mock_session:
            mock_db = Mock()
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            mock_session.return_value.__enter__.return_value = mock_db
            
            scheduled_seo_sitemap_update()
            # Should complete without error


def test_setup_scheduled_tasks():
    """Test setup_scheduled_tasks."""
    result = setup_scheduled_tasks()
    assert result is None