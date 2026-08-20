"""
Periodic scheduler using periodiq to trigger dramatiq actors on cron schedules.
This runs as a separate process alongside the dramatiq worker.

This module imports the broker and all scheduled actors to ensure they are registered
when periodiq imports this module.
"""

import logging
from apps.workers.tasks import broker
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    scheduled_seo_sitemap_update
)

logger = logging.getLogger(__name__)

logger.info("Periodic scheduler module loaded - actors are registered via periodic decorator in scheduler.py")