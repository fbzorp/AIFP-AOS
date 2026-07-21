import os
import logging

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from apps.api.config import settings

logger = logging.getLogger(__name__)

# Configure Dramatiq with Redis using the environment-aware settings.
redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
redis_broker = RedisBroker(url=redis_url)
dramatiq.set_broker(redis_broker)


@dramatiq.actor
async def process_agent_task(agent_name: str, task_data: dict):
    """Background task for processing agent work."""
    logger.info(f"Processing task for agent: {agent_name}")
    # Task processing logic will be implemented per agent
    return {"status": "processed", "agent": agent_name}


@dramatiq.actor
async def publish_content(content_id: str, platform: str):
    """Background task for publishing content to social platforms."""
    logger.info(f"Publishing content {content_id} to {platform}")
    # Publishing logic will be implemented
    return {"status": "published", "content_id": content_id, "platform": platform}
