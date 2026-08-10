"""
Scheduled publishing tasks for autonomous content publishing.
Avoids rate limits by staggering agent publishing intervals.
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


def scheduled_publisher_agent_task(agent_name: str):
    """
    Base function for scheduled publishing tasks.
    """
    logger.info(f"Running scheduled publisher for {agent_name}")
    
    with get_sync_session() as session:
        # Get approved content for this agent that hasn't been published yet
        result = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.author_agent == agent_name,
                ContentItemModel.status == "approved",
                ContentItemModel.post_id.is_(None)
            ).order_by(ContentItemModel.created_at).limit(1)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            logger.info(f"No approved content to publish for {agent_name}")
            return
        
        # Get approval
        approval = session.execute(
            select(ApprovalModel).where(
                ApprovalModel.content_id == content.id,
                ApprovalModel.status == "approved"
            ).order_by(ApprovalModel.created_at.desc()).limit(1)
        ).scalar_one_or_none()
        
        if not approval:
            logger.warning(f"No valid approval found for {content.id}")
            return
        
        # Publish content
        try:
            from apps.workers.tasks import publish_content
            result = publish_content(content.id, approval.id, approval.draft_hash)
            logger.info(f"Published {content.id} for {agent_name}: {result}")
        except Exception as e:
            logger.error(f"Publisher task failed for {agent_name}: {e}")
            raise


@dramatiq.actor(periodic=cron("*/30 * * * *"))
def scheduled_publisher_agent_task_founder():
    """Scheduled task for Founder Content to publish every 30 minutes."""
    scheduled_publisher_agent_task("Founder Content")


@dramatiq.actor(periodic=cron("*/45 * * * *"))
def scheduled_publisher_agent_task_technical():
    """Scheduled task for Technical Content to publish every 45 minutes."""
    scheduled_publisher_agent_task("Technical Content")


@dramatiq.actor(periodic=cron("*/60 * * * *"))
def scheduled_publisher_agent_task_seo():
    """Scheduled task for SEO Content to publish every 60 minutes."""
    scheduled_publisher_agent_task("SEO Content")


@dramatiq.actor(periodic=cron("0 */6 * * *"))
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


def setup_scheduled_tasks():
    """
    Setup scheduled tasks for autonomous publishing.
    Note: periodiq handles scheduling via decorators, so this function is informational.
    """
    logger.info("Periodiq middleware installed - automatic scheduling enabled")
    logger.info("Scheduled tasks:")
    logger.info("- Founder Content: Every 30 minutes (*/30 * * * *)")
    logger.info("- Technical Content: Every 45 minutes (*/45 * * * *)")
    logger.info("- SEO Content: Every 60 minutes (*/60 * * * *)")
    logger.info("- Telegram Republisher: Every 6 hours (0 */6 * * *)")
    
    return
