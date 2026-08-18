"""Tests for periodic scheduler configuration."""

from apps.workers.periodic_scheduler import SCHEDULES


def test_periodic_scheduler_configured():
    """Test that periodic scheduler has expected schedules configured."""
    assert len(SCHEDULES) > 0
    
    # Verify each schedule is a tuple of (cron_expr, actor_name)
    for schedule in SCHEDULES:
        assert isinstance(schedule, tuple)
        assert len(schedule) == 2
        cron_expr, actor_name = schedule
        # cron_expr is a CronSpec object from periodiq
        assert hasattr(cron_expr, '__str__')
        assert isinstance(actor_name, str)


def test_periodic_scheduler_has_seo_sitemap():
    """Test that SEO sitemap update task is scheduled."""
    actor_names = [schedule[1] for schedule in SCHEDULES]
    assert "scheduled_seo_sitemap_update" in actor_names
