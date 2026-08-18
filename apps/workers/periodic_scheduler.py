"""
Periodic scheduler using periodiq to trigger dramatiq actors on cron schedules.
This runs as a separate process alongside the dramatiq worker.
"""

import logging
from periodiq import cron
from apps.workers.tasks import broker
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    scheduled_seo_sitemap_update
)

logger = logging.getLogger(__name__)

# Configure periodic schedules for periodiq
SCHEDULES = [
    # Autonomous publisher: every 15 minutes
    (cron("*/15 * * * *"), scheduled_autonomous_publisher.actor_name),
    # Telegram republisher: every 6 hours
    (cron("0 */6 * * *"), scheduled_telegram_republisher.actor_name),
    # Telegram digest: every 6 hours (offset by 3 hours from republisher)
    (cron("0 3,9,15,21 * * *"), scheduled_telegram_digest.actor_name),
    # SEO content generator: every 12 hours
    (cron("0 */12 * * *"), scheduled_seo_content_generator.actor_name),
    # SEO sitemap update: every 6 hours
    (cron("0 */6 * * *"), scheduled_seo_sitemap_update.actor_name),
]

logger.info(f"Configured {len(SCHEDULES)} periodic tasks:")
for cron_expr, actor_name in SCHEDULES:
    logger.info(f"- {actor_name}: {cron_expr}")