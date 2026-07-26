
import os
import logging
import asyncio
import dramatiq
from sqlalchemy.sql import func
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
    follow_on_tasks = []
    
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
            
            # Day 8-9: Connect news-to-content chain
            if task.task_type == "Content Strategy" and result.get("outcome") == "weekly_plan_created":
                item_ids = result.get("items", [])
                for item_id in item_ids:
                    # Get the item to decide Technical vs Founder routing
                    item = session.query(ContentItemModel).filter(ContentItemModel.id == item_id).first()
                    if not item: continue
                    
                    # Decide routing: Technical for developer/SDK/technical formats, Founder otherwise
                    target_agent = "Founder Content"
                    tech_keywords = ["technical", "sdk", "tutorial", "code", "mcp", "x402", "developer"]
                    if any(kw in (item.format or "").lower() for kw in tech_keywords) or \
                       any(kw in (item.objective or "").lower() for kw in tech_keywords):
                        target_agent = "Technical Content"
                    
                    # Create follow-on task row
                    new_task = TaskModel(
                        task_type=target_agent,
                        input_data={"content_item_id": item_id},
                        status="pending"
                    )
                    session.add(new_task)
                    session.flush() # Ensure ID is generated
                    
                    # Record audit event inside the transaction
                    record_event(session, "System", "task_enqueued", f"Enqueued {target_agent} for item {item_id}", {"task_id": new_task.id, "item_id": item_id})
                    
                    # Collect ID for dispatch AFTER commit
                    follow_on_tasks.append(new_task.id)

            elif task.task_type in ["Technical Content", "Founder Content"] and result.get("outcome") in ["tutorial_generated", "founder_draft_ready"]:
                item_id = result.get("item_id")
                if item_id:
                    # Create follow-on task row
                    new_task = TaskModel(
                        task_type="Compliance & Brand",
                        input_data={"content_item_id": item_id},
                        status="pending"
                    )
                    session.add(new_task)
                    session.flush() # Ensure ID is generated
                    
                    # Record audit event inside the transaction
                    record_event(session, "System", "task_enqueued", f"Enqueued Compliance & Brand for item {item_id}", {"task_id": new_task.id, "item_id": item_id})
                    
                    # Collect ID for dispatch AFTER commit
                    follow_on_tasks.append(new_task.id)

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task.status = "failed"
            task.error = str(e)
            record_event(session, "System", "task_failed", f"Failed task {task_id}: {e}", {"task_id": task_id})
            raise # Re-raise for Dramatiq retry

    # Dispatch follow-on tasks AFTER the session block has committed
    for next_task_id in follow_on_tasks:
        logger.info(f"Dispatching follow-on task {next_task_id}")
        run_agent_task.send(next_task_id)

async def _perform_publish_logic(session, content_id: str, approval_id: str, draft_hash: str):
    record_event(session, "System", "publish_requested", f"Publish requested for {content_id}", {"approval_id": approval_id})
    
    content = session.query(ContentItemModel).filter(ContentItemModel.id == content_id).first()
    if not content:
        record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: content not found", {"content_id": content_id})
        raise ValueError("Content not found")

    if content.status != "approved":
        record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: status is {content.status}", {"content_id": content_id})
        raise ValueError(f"Content status is {content.status}, must be approved")

    # Idempotency check
    if content.status == "published" or content.post_id:
        record_event(session, "System", "publish_skipped_idempotent", f"Publish skipped for {content_id}: already published", {"content_id": content_id, "existing_post_id": content.post_id})
        return {"status": "already_published", "content_id": content_id, "post_id": content.post_id}

    engine = PolicyEngine()
    if not engine.validate_approval(session, approval_id, draft_hash):
        record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: invalid approval hash or expiry", {"approval_id": approval_id})
        raise ValueError("Invalid approval")
        
    # Real publication logic
    from apps.integrations.moltbook.client import MoltbookClient
    
    # Enforce allowlist
    target_submolt = content.channel.lower()
    allowed_submolts = getattr(settings, "MOLTBOOK_ALLOWED_SUBMOLTS", "general").split(",")
    if target_submolt not in [s.strip().lower() for s in allowed_submolts]:
        record_event(session, "System", "publish_denied", f"Submolt {target_submolt} not in allowlist", {"content_id": content_id})
        raise ValueError(f"Submolt {target_submolt} not in allowlist")

    try:
        async with MoltbookClient() as client:
            pub_result = await client.publish_post(
                submolt=target_submolt,
                title=content.title,
                body=content.body or str(content.variants)
            )
        
        content.post_id = pub_result.get("post_id")
        content.post_url = pub_result.get("post_url")
        content.published_at = func.now()
        content.status = "published"
        
        record_event(
            session, 
            "System", 
            "content_published", 
            f"Published {content_id} to {target_submolt}", 
            {
                "content_id": content_id, 
                "post_id": content.post_id, 
                "post_url": content.post_url,
                "dry_run": pub_result.get("dry_run", False)
            }
        )
        session.commit()
        return {"status": "published", "content_id": content_id, "post_id": content.post_id, "post_url": content.post_url, "dry_run": pub_result.get("dry_run", False)}
        
    except Exception as e:
        logger.error(f"Publishing failed for {content_id}: {e}")
        content.publish_error = str(e)
        record_event(session, "System", "publish_failed", f"Failed to publish {content_id}: {e}", {"content_id": content_id})
        session.commit()
        raise

@dramatiq.actor
def publish_content(content_id: str, approval_id: str, draft_hash: str):
    """
    Gated executor for publishing content.
    """
    with get_sync_session() as session:
        return asyncio.run(_perform_publish_logic(session, content_id, approval_id, draft_hash))
