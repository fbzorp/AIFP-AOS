import os
import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from apps.api.config import settings
from apps.core.policy.engine import PolicyEngine

# Setup Dramatiq Redis Broker
broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

@dramatiq.actor
def publish_content(content_id: str, approval_id: str, draft_hash: str):
    """
    Gated executor: checks approval, hash, and expiry before publishing.
    This is a synchronous actor as Dramatiq does not support async actors by default.
    """
    logger.info(f"Worker received publish request for content {content_id}")
    
    engine = PolicyEngine()
    if not engine.validate_approval(approval_id, draft_hash):
        logger.error(f"Approval validation failed for content {content_id}")
        raise ValueError("Invalid approval")
        
    # TODO: Implement actual publication logic (Moltbook API call)
    logger.info(f"Content {content_id} successfully validated and ready for publication")
    
    return {"status": "published", "content_id": content_id}

# Content agents ONLY prepare drafts, no direct publish
