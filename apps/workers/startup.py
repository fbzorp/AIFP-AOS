"""
Worker startup module - initializes scheduled tasks when worker starts.
"""

import logging
from apps.workers.scheduler import setup_scheduled_tasks

logger = logging.getLogger(__name__)

def initialize_worker():
    """Initialize worker with scheduled tasks."""
    logger.info("Initializing worker with scheduled tasks...")
    setup_scheduled_tasks()
    logger.info("Worker initialization complete")
