"""
Worker initialization module to handle circular import issues.
This module initializes the worker with scheduled tasks.
"""

def initialize_worker():
    """Initialize worker with scheduled tasks."""
    from apps.workers.scheduler import setup_scheduled_tasks
    setup_scheduled_tasks()
