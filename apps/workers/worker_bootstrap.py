"""
Worker bootstrap file to initialize Dramatiq worker.
This file is used as the Dramatiq entry point.
"""

# Import tasks to ensure all actors are registered
from apps.workers.tasks import broker, dramatiq

# Import scheduler to register actors
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    setup_scheduled_tasks
)

# Setup scheduled tasks (informational only since we removed cron)
setup_scheduled_tasks()

# Export for Dramatiq CLI
__all__ = ['broker', 'dramatiq']
