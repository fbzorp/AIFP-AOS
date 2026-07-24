import os
import logging
import asyncio
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from apps.api.config import settings
from apps.models.base import get_sync_session
from apps.models.task import TaskModel
from apps.models.content_item import ContentItemModel
from apps.core.policy.engine import PolicyEngine
from apps.core.audit.service import record_event
from apps.agents.registry import get_agent

# Setup Dramatiq Redis Broker
broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

@dramatiq.actor(max_retries=3, min_backoff=1000, max_backoff=30000)
def run_agent_task(task_id: str):
    """
    Generic task runner with retries and audit logging.
    """
    with get_sync_session() as session:
        task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        # Idempotency check
        if task.status == "succeeded":
            logger.info(f"Task {task_id} already succeeded, skipping")
            return

        try:
            task.status = "running"
            session.flush()
            record_event(session, "System", "task_started", f"Started task {task_id}", {"task_id": task_id})
            
            # Resolve agent
            agent_instance = get_agent(task.task_type)
            if not agent_instance:
                raise ValueError(f"Agent for {task.task_type} not found")

            # Run agent (sync wrapper for async execute)
            result = asyncio.run(agent_instance.execute(task.input_data))
            
            task.status = "succeeded"
            task.result = result
            record_event(session, agent_instance.name, "task_succeeded", f"Completed task {task_id}", {"task_id": task_id})
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task.status = "failed"
            task.error = str(e)
            record_event(session, "System", "task_failed", f"Failed task {task_id}: {e}", {"task_id": task_id})
            raise # Re-raise for Dramatiq retry

@dramatiq.actor
def publish_content(content_id: str, approval_id: str, draft_hash: str):
    """
    Gated executor for publishing content.
    """
    with get_sync_session() as session:
        record_event(session, "System", "publish_requested", f"Publish requested for {content_id}", {"approval_id": approval_id})
        
        content = session.query(ContentItemModel).filter(ContentItemModel.id == content_id).first()
        if not content:
            record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: content not found", {"content_id": content_id})
            raise ValueError("Content not found")

        if content.status != "approved":
            record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: status is {content.status}", {"content_id": content_id})
            raise ValueError(f"Content status is {content.status}, must be approved")

        engine = PolicyEngine()
        if not engine.validate_approval(session, approval_id, draft_hash):
            record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: invalid approval hash or expiry", {"approval_id": approval_id})
            raise ValueError("Invalid approval")
            
        # Integration point for Days 10-12
        logger.info(f"Content {content_id} ready for Moltbook publication")
        record_event(session, "System", "publish_ready", f"Content {content_id} validated and ready for Moltbook", {"content_id": content_id})
        
        return {"status": "ready_for_integration", "content_id": content_id}
