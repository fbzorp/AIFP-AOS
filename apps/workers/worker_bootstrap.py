"""
Worker bootstrap file to initialize scheduled tasks without circular imports.
This file is used as the Dramatiq/Periodiq entry point.
"""

# Import tasks to ensure all actors are registered
from apps.workers.tasks import broker, dramatiq

# Import scheduler to register periodic tasks with periodiq
from apps.workers.scheduler import (
    scheduled_publisher_agent_task_founder,
    scheduled_publisher_agent_task_technical, 
    scheduled_publisher_agent_task_seo,
    scheduled_telegram_republisher,
    setup_scheduled_tasks
)

# Setup scheduled tasks
setup_scheduled_tasks()

# Export for Dramatiq CLI
__all__ = ['broker', 'dramatiq']
