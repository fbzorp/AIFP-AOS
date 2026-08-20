"""
Scheduled publishing tasks for autonomous content publishing.
Unified publisher actor handles all approved content for simpler, more robust scheduling.
"""

import logging
import asyncio
import dramatiq
from periodiq import cron
from apps.api.config import settings
from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from sqlalchemy import select

logger = logging.getLogger(__name__)


def scheduled_autonomous_publisher():
    """
    Unified autonomous publisher that processes ALL approved content.
    Runs every 15 minutes to publish approved content in batches of 5.
    This replaces the per-agent cron actors for simpler, more robust scheduling.
    """
    logger.info("Running unified autonomous publisher")
    
    with get_sync_session() as session:
        # Get all approved content that hasn't been published yet
        result = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.status == "approved",
                ContentItemModel.post_id.is_(None)
            ).order_by(ContentItemModel.created_at).limit(5)
        )
        approved_content = result.scalars().all()
        
        if not approved_content:
            logger.info("No approved content to publish")
            return
        
        logger.info(f"Found {len(approved_content)} approved content items to publish")
        
        # Process each content item
        published_count = 0
        for content in approved_content:
            try:
                # Get approval for this content
                approval = session.execute(
                    select(ApprovalModel).where(
                        ApprovalModel.content_id == content.id,
                        ApprovalModel.status == "approved"
                    ).order_by(ApprovalModel.created_at.desc()).limit(1)
                ).scalar_one_or_none()
                
                if not approval:
                    logger.warning(f"No valid approval found for {content.id}")
                    continue
                
                # Publish content
                from apps.workers.tasks import _perform_publish_logic
                result = asyncio.run(_perform_publish_logic(session, content.id, approval.id, approval.draft_hash))
                
                if result.get("status") == "published":
                    published_count += 1
                    logger.info(f"Successfully published {content.id} ({content.author_agent})")
                else:
                    logger.warning(f"Publishing failed for {content.id}: {result}")
                    
            except Exception as e:
                logger.error(f"Error publishing {content.id}: {e}")
                # Continue with next item rather than failing the whole batch
        
        logger.info(f"Unified publisher complete: {published_count}/{len(approved_content)} items published")


def scheduled_telegram_republisher():
    """
    Scheduled task to republish SEO content to Telegram channel.
    Runs every 6 hours to avoid overwhelming the channel.
    """
    logger.info("Running scheduled Telegram republisher")

    from apps.agents.registry import get_agent

    agent = get_agent("Telegram Republisher")
    if not agent:
        logger.error("Telegram Republisher agent not found")
        return

    try:
        result = asyncio.run(agent.execute({}))
        logger.info(f"Telegram republisher result: {result}")
    except Exception as e:
        logger.error(f"Telegram republisher task failed: {e}")
        raise


def scheduled_telegram_digest():
    """
    Scheduled task to post 6-hour digest of all published content to Telegram channel.
    Runs every 6 hours to highlight all posts across all agents/channels.
    """
    logger.info("Running scheduled Telegram digest")

    from apps.agents.registry import get_agent

    agent = get_agent("Telegram Republisher")
    if not agent:
        logger.error("Telegram Republisher agent not found")
        return

    try:
        result = asyncio.run(agent.execute({"mode": "digest"}))
        logger.info(f"Telegram digest result: {result}")
    except Exception as e:
        logger.error(f"Telegram digest task failed: {e}")
        raise


def scheduled_seo_content_generator():
    """
    Scheduled task to generate SEO content on a regular interval.
    Runs every 12 hours to generate new SEO content via Content Strategy agent.
    """
    logger.info("Running scheduled SEO content generator")

    from apps.models.task import TaskModel
    from apps.models.base import get_sync_session
    from apps.workers.tasks import run_agent_task

    with get_sync_session() as session:
        # Create a Content Strategy task with SEO-oriented objective
        task = TaskModel(
            task_type="Content Strategy",
            input_data={
                "objective": "Generate SEO-optimized content for Google search",
                "channel": "google",
                "format": "article",
                "target_audience": "developers and AI enthusiasts"
            },
            status="pending"
        )
        session.add(task)
        session.flush()

        logger.info(f"Created Content Strategy task {task.id} for SEO content generation")

        # Dispatch the task
        run_agent_task.send(task.id)
        logger.info(f"Dispatched SEO content generation task {task.id}")


def scheduled_seo_sitemap_update():
    """
    Scheduled task to rebuild sitemap and check indexing status for SEO pages.
    Runs every 6 hours to ensure sitemap is current and indexing status is updated.
    """
    logger.info("Running scheduled SEO sitemap update")

    from apps.integrations.publishing.seo_page_publisher import SeoPagePublisher
    from apps.models.content_item import ContentItemModel
    from sqlalchemy import select

    try:
        # Rebuild sitemap
        publisher = SeoPagePublisher()
        publisher._ensure_initialized()
        publisher._update_sitemap_and_robots()
        logger.info("SEO sitemap and robots.txt regenerated")

        # Update indexing status for published SEO pages
        with get_sync_session() as session:
            # Get all published SEO content
            result = session.execute(
                select(ContentItemModel).where(
                    ContentItemModel.channel.in_(["google", "seo", "blog"]),
                    ContentItemModel.status == "published",
                    ContentItemModel.post_url.isnot(None)
                )
            )
            seo_pages = result.scalars().all()

            logger.info(f"Found {len(seo_pages)} published SEO pages to check indexing status")

            # In a real implementation, this would check Google Search Console API
            # For now, we'll just log the status
            for page_id in seo_pages:
                # Update indexing status would go here based on Search Console API
                # For now, we leave status as-is
                pass

        logger.info("SEO sitemap update complete")

    except Exception as e:
        logger.error(f"SEO sitemap update failed: {e}")
        raise


# Register actors with periodiq cron scheduling
scheduled_autonomous_publisher = dramatiq.actor(periodic=cron("*/15 * * * *"))(scheduled_autonomous_publisher)
scheduled_telegram_republisher = dramatiq.actor(periodic=cron("0 */6 * * *"))(scheduled_telegram_republisher)
scheduled_telegram_digest = dramatiq.actor(periodic=cron("0 3,9,15,21 * * *"))(scheduled_telegram_digest)
scheduled_seo_content_generator = dramatiq.actor(periodic=cron("0 */12 * * *"))(scheduled_seo_content_generator)
scheduled_seo_sitemap_update = dramatiq.actor(periodic=cron("0 */6 * * *"))(scheduled_seo_sitemap_update)

logger.info("Actors registered for scheduled tasks (periodiq scheduler will trigger them)")


def setup_scheduled_tasks():
    """
    Setup scheduled tasks for autonomous publishing.
    Uses periodiq for cron scheduling with Redis backend.
    """
    logger.info("Dramatiq actors registered for scheduled tasks")
    logger.info("Scheduled tasks with cron scheduling:")
    logger.info("- Unified Autonomous Publisher: Every 15 minutes (*/15 * * * *)")
    logger.info("- Telegram Republisher: Every 6 hours (0 */6 * * *)")
    logger.info("- Telegram Digest: Every 6 hours at 3,9,15,21 UTC (0 3,9,15,21 * * *)")
    logger.info("- SEO Content Generator: Every 12 hours (0 */12 * * *)")
    logger.info("- SEO Sitemap Update: Every 6 hours (0 */6 * * *)")
    logger.info("Tasks read database state on startup for automatic resume after restart")
    
    return
