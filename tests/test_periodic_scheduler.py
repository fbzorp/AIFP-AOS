"""Tests for periodic scheduler configuration."""

from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    scheduled_seo_sitemap_update
)


def test_periodic_scheduler_configured():
    """Test that periodic scheduler has expected actors configured with periodic option."""
    # Verify all expected actors are registered
    assert scheduled_autonomous_publisher is not None
    assert scheduled_telegram_republisher is not None
    assert scheduled_telegram_digest is not None
    assert scheduled_seo_content_generator is not None
    assert scheduled_seo_sitemap_update is not None
    
    # Verify they have actor_name attribute
    assert hasattr(scheduled_autonomous_publisher, 'actor_name')
    assert hasattr(scheduled_telegram_republisher, 'actor_name')
    assert hasattr(scheduled_telegram_digest, 'actor_name')
    assert hasattr(scheduled_seo_content_generator, 'actor_name')
    assert hasattr(scheduled_seo_sitemap_update, 'actor_name')
    
    # Verify they have periodic option set
    assert scheduled_autonomous_publisher.options.get("periodic") is not None
    assert scheduled_telegram_republisher.options.get("periodic") is not None
    assert scheduled_telegram_digest.options.get("periodic") is not None
    assert scheduled_seo_content_generator.options.get("periodic") is not None
    assert scheduled_seo_sitemap_update.options.get("periodic") is not None


def test_periodic_scheduler_has_seo_sitemap():
    """Test that SEO sitemap update task is scheduled."""
    assert scheduled_seo_sitemap_update is not None
    assert scheduled_seo_sitemap_update.actor_name == "scheduled_seo_sitemap_update"
    assert scheduled_seo_sitemap_update.options.get("periodic") is not None
