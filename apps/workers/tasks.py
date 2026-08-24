
import os
import logging
import asyncio
import dramatiq
from datetime import datetime, timedelta, timezone
from sqlalchemy.sql import func
from dramatiq.brokers.redis import RedisBroker
from apps.api.config import settings
from apps.models.base import get_sync_session
from apps.models.task import TaskModel
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.core.policy.engine import PolicyEngine, compute_draft_hash
from apps.core.audit.service import record_event
from apps.agents.registry import get_agent

# Setup Dramatiq Redis Broker
broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

# Add periodiq middleware for cron scheduling
try:
    from periodiq import PeriodiqMiddleware
    broker.add_middleware(PeriodiqMiddleware(skip_delay=30))
    logger.info("Periodiq middleware installed for scheduled tasks")
except ImportError:
    logger.warning("Periodiq not available, using manual scheduling")

# Import periodic actors to register them on the broker
# This must happen AFTER the PeriodiqMiddleware is installed
from apps.workers.scheduler import (
    scheduled_autonomous_publisher,
    scheduled_telegram_republisher,
    scheduled_telegram_digest,
    scheduled_seo_content_generator,
    scheduled_seo_sitemap_update
)

# Export for Dramatiq CLI
__all__ = ['broker']

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
                    # Get the item to decide Technical vs Founder vs SEO routing
                    item = session.query(ContentItemModel).filter(ContentItemModel.id == item_id).first()
                    if not item: continue
                    
                    # Decide routing: SEO for google/seo channels, Technical for developer/SDK/technical formats, Founder otherwise
                    target_agent = "Founder Content"
                    seo_keywords = ["google", "seo", "article", "blog"]
                    tech_keywords = ["technical", "sdk", "tutorial", "code", "mcp", "x402", "developer"]
                    
                    # Check for SEO/Google channel or format
                    if any(kw in (item.channel or "").lower() for kw in seo_keywords) or \
                       any(kw in (item.format or "").lower() for kw in seo_keywords) or \
                       any(kw in (item.objective or "").lower() for kw in seo_keywords):
                        target_agent = "SEO Content"
                    # Check for Technical keywords
                    elif any(kw in (item.format or "").lower() for kw in tech_keywords) or \
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

            elif task.task_type in ["Technical Content", "Founder Content", "SEO Content"] and result.get("outcome") in ["tutorial_generated", "founder_draft_ready", "seo_content_generated"]:
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

            elif task.task_type == "Compliance & Brand" and result.get("outcome") == "compliance_passed":
                item_id = result.get("item_id")
                if item_id:
                    # ALL content (including SEO) transitions to pending_review for human approval
                    content = session.query(ContentItemModel).filter(ContentItemModel.id == item_id).first()
                    if content:
                        content.status = "pending_review"
                        record_event(
                            session,
                            agent_name="System",
                            event_type="compliance_pending_review",
                            message=f"Compliance passed, pending human review: {content.title}",
                            metadata={"content_id": item_id, "author_agent": content.author_agent}
                        )

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

    # Idempotency check - already published content should be handled gracefully
    if content.status == "published" or content.post_id:
        record_event(session, "System", "publish_skipped_idempotent", f"Publish skipped for {content_id}: already published", {"content_id": content_id, "existing_post_id": content.post_id})
        return {"status": "already_published", "content_id": content_id, "post_id": content.post_id}

    if content.status != "approved":
        record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: status is {content.status}", {"content_id": content_id})
        raise ValueError(f"Content status is {content.status}, must be approved")

    engine = PolicyEngine()
    if not engine.validate_approval(session, approval_id, draft_hash):
        record_event(session, "System", "publish_denied", f"Publish denied for {content_id}: invalid approval hash or expiry", {"approval_id": approval_id})
        raise ValueError("Invalid approval")
        
    # Channel-agnostic publication logic
    from apps.integrations.publishing import get_publisher
    
    try:
        # Resolve publisher based on content.channel and content.author_agent
        publisher = get_publisher(content.channel, agent_name=content.author_agent)
        
        # Prepare publisher-specific parameters
        publisher_params = {"content_id": content_id}
        if content.channel.lower() in ["moltbook", "general", "aifintech", "aiagents"]:
            publisher_params["submolt"] = content.channel.lower()
        elif content.channel.lower() == "google":
            # For google channel, route to google submolt on Moltbook
            publisher_params["submolt"] = "google"
        
        # Call publisher
        async with publisher as pub_client:
            pub_result = await pub_client.publish_post(
                title=content.title,
                body=content.body or str(content.variants),
                channel=content.channel,  # Pass channel for routing decisions
                **publisher_params
            )

        # Check if publishing was successful
        if not pub_result.get("success"):
            raise ValueError(f"Publishing failed: {pub_result.get('error', 'Unknown error')}")

        # Branch on dry_run flag to preserve integrity
        is_dry_run = pub_result.get("dry_run", False)

        if is_dry_run:
            # Dry-run: do NOT stamp fake post_id/post_url/published_at
            content.status = "dry_run"
            # Leave post_id, post_url, published_at as NULL (do not set fake values)

            record_event(
                session,
                "System",
                "content_dry_run",
                f"Dry-run published {content_id} to {content.channel}",
                {
                    "content_id": content_id,
                    "dry_run": True,
                    "channel": content.channel
                }
            )
            session.commit()
            return {"status": "dry_run", "content_id": content_id, "dry_run": True}
        else:
            # Real publication: stamp real post_id/post_url/published_at
            content.post_id = pub_result.get("post_id")
            content.post_url = pub_result.get("post_url")
            content.published_at = func.now()
            content.status = "published"

            # Capture SEO metadata if available (from SeoPagePublisher)
            if pub_result.get("canonical_url"):
                content.canonical_url = pub_result.get("canonical_url")
            if pub_result.get("target_keyword"):
                content.target_keyword = pub_result.get("target_keyword")
            if pub_result.get("meta_title"):
                content.meta_title = pub_result.get("meta_title")
            if pub_result.get("meta_description"):
                content.meta_description = pub_result.get("meta_description")
            if pub_result.get("indexing_status"):
                content.indexing_status = pub_result.get("indexing_status")

            record_event(
                session,
                "System",
                "content_published",
                f"Published {content_id} to {content.channel}",
                {
                    "content_id": content_id,
                    "post_id": content.post_id,
                    "post_url": content.post_url,
                    "dry_run": False,
                    "channel": content.channel
                }
            )
            session.commit()

            # Trigger Telegram republisher for successful publishes with URLs
            if content.post_url:
                try:
                    from apps.agents.registry import get_agent
                    telegram_agent = get_agent("Telegram Republisher")
                    if telegram_agent:
                        logger.info(f"Triggering Telegram republisher for {content_id}")
                        # Send republish task with content_id
                        trigger_telegram_republish.send(content_id)
                except Exception as e:
                    logger.warning(f"Failed to trigger Telegram republisher: {e}")

            return {"status": "published", "content_id": content_id, "post_id": content.post_id, "post_url": content.post_url, "dry_run": False}
        
    except Exception as e:
        logger.error(f"Publishing failed for {content_id}: {e}")
        content.publish_error = str(e)
        record_event(session, "System", "publish_failed", f"Failed to publish {content_id}: {e}", {"content_id": content_id})
        session.commit()
        raise

@dramatiq.actor
def trigger_telegram_republish(content_id: str):
    """
    Trigger Telegram republisher for a specific content item.
    """
    logger.info(f"Telegram republish triggered for {content_id}")
    
    try:
        from apps.agents.registry import get_agent
        agent = get_agent("Telegram Republisher")
        if not agent:
            logger.error("Telegram Republisher agent not found")
            return
        
        result = asyncio.run(agent.execute({"content_id": content_id}))
        logger.info(f"Telegram republish result: {result}")
    except Exception as e:
        logger.error(f"Telegram republish task failed: {e}")
        raise

@dramatiq.actor
def publish_content(content_id: str, approval_id: str, draft_hash: str):
    """
    Gated executor for publishing content.
    """
    with get_sync_session() as session:
        return asyncio.run(_perform_publish_logic(session, content_id, approval_id, draft_hash))
