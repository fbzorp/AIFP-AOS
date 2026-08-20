"""
Periodic scheduler using periodiq to trigger dramatiq actors on cron schedules.
This runs as a separate process alongside the dramatiq worker.

Note: Actors are now registered with periodiq decorator in scheduler.py
This file is kept for compatibility but scheduling is defined in scheduler.py
"""

import logging

logger = logging.getLogger(__name__)

logger.info("Periodic scheduler module loaded - actors are registered via periodiq decorator in scheduler.py")