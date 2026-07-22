import os
import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from apps.api.config import settings
from apps.core.policy.engine import PolicyEngine

# ... broker setup ...

@dramatiq.actor
async def publish_content(content_id: str, approval_id: str, draft_hash: str):
    # Gated executor: check approval, hash, expiry
    engine = PolicyEngine()
    if not engine.validate_approval(approval_id, draft_hash):
        raise ValueError("Invalid approval")
    # Publish logic (idempotent)
    return {"status": "published"}

# Content agents ONLY prepare drafts, no direct publish