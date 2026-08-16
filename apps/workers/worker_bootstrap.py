"""
Worker bootstrap file to initialize scheduled tasks without circular imports.
This file is used as the Dramatiq/Periodiq entry point.
"""

# Import tasks to ensure all actors are registered
from apps.workers.tasks import broker, dramatiq

# Import scheduler to register periodic tasks with periodiq
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    setup_scheduled_tasks
)

# Setup scheduled tasks
setup_scheduled_tasks()

# Export for Dramatiq CLI
__all__ = ['broker', 'dramatiq']
