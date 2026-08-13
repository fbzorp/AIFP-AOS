"""
Telegram Republisher Agent
Monitors for successful content from all agents and republishes to the "zorpresearch" channel.
Uses DeepSeek reasoning model for execution decisions.
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, desc

from apps.agents.base import BaseAgent
from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from apps.integrations.telegram.client import TelegramClient
from apps.api.config import settings
import litellm

logger = logging.getLogger(__name__)


class TelegramRepublisherAgent(BaseAgent):
    """Agent that republishes successful SEO content to Telegram channel."""
    
    def __init__(self):
        super().__init__(
            name="Telegram Republisher",
            role="Content Syndication",
            description="Monitors successful SEO content and republishes to Telegram channel"
        )
        self.telegram_client = None
        self.channel_id = "zorpresearch"
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Telegram republishing workflow.

        Args:
            input_data: May contain specific content_id to republish, or empty for auto-discovery/digest

        Returns:
            Dict with execution results
        """
        try:
            if input_data.get("mode") == "digest":
                # Build and post 6-hour digest of all posts
                result = await self._build_all_posts_digest()
            elif input_data.get("content_id"):
                # Republish specific content
                result = await self._republish_specific_content(input_data["content_id"])
            else:
                # Auto-discover and republish recent SEO content
                result = await self._auto_discover_and_republish()

            return {
                "agent": self.name,
                "outcome": result.get("outcome", "completed"),
                "report": result
            }

        except Exception as e:
            logger.error(f"Telegram republishing failed: {e}")
            return {
                "agent": self.name,
                "outcome": "failed",
                "error": str(e)
            }
    
    async def _republish_specific_content(self, content_id: str) -> Dict[str, Any]:
        """Republish a specific content item to Telegram."""
        with get_sync_session() as session:
            content = session.query(ContentItemModel).filter(
                ContentItemModel.id == content_id
            ).first()
            
            if not content:
                return {"error": f"Content {content_id} not found"}
            
            if content.status != "published":
                return {"error": f"Content {content_id} not published (status: {content.status})"}
            
            if not content.post_url:
                return {"error": f"Content {content_id} has no post_url"}
            
            # Use DeepSeek reasoning to decide if content should be republished
            should_publish = await self._evaluate_content_for_republishing(content)
            
            if not should_publish:
                return {"content_id": content_id, "decision": "not_published", "reason": "AI evaluation decided against republishing"}
            
            # Republish to Telegram
            telegram_post = await self._publish_to_telegram(content)
            
            return {
                "content_id": content_id,
                "original_post_url": content.post_url,
                "telegram_post_id": telegram_post.get("post_id"),
                "telegram_post_url": telegram_post.get("post_url"),
                "decision": "published",
                "agent": content.author_agent
            }
    
    async def _auto_discover_and_republish(self) -> Dict[str, Any]:
        """Auto-discover recent SEO content and republish to Telegram."""
        with get_sync_session() as session:
            # Get recently published SEO content from all agents (last 24 hours)
            cutoff = datetime.now() - timedelta(hours=24)

            seo_content = session.query(ContentItemModel).filter(
                ContentItemModel.status == "published",
                ContentItemModel.published_at >= cutoff,
                ContentItemModel.post_url.isnot(None),
                ContentItemModel.author_agent == "SEO Content"
            ).order_by(desc(ContentItemModel.published_at)).limit(10).all()

            results = []

            for content in seo_content:
                # Use DeepSeek reasoning to evaluate
                should_publish = await self._evaluate_content_for_republishing(content)

                if should_publish:
                    telegram_post = await self._publish_to_telegram(content)
                    results.append({
                        "content_id": content.id,
                        "original_post_url": content.post_url,
                        "telegram_post_id": telegram_post.get("post_id"),
                        "telegram_post_url": telegram_post.get("post_url"),
                        "agent": content.author_agent,
                        "title": content.title
                    })

            return {
                "total_seo_content": len(seo_content),
                "republished_count": len(results),
                "results": results
            }
    
    async def _evaluate_content_for_republishing(self, content: ContentItemModel) -> bool:
        """
        Use DeepSeek reasoning model to evaluate if content should be republished.
        
        Args:
            content: ContentItemModel to evaluate
        
        Returns:
            bool: True if content should be republished
        """
        if not settings.DEEPSEEK_REASONING_MODEL:
            logger.warning("DeepSeek reasoning model not configured, defaulting to publish")
            return True
        
        prompt = f"""
        Evaluate this SEO content for republishing to the "zorpresearch" Telegram channel.

Content Title: {content.title}
Content Body: {content.body[:500] if content.body else content.variants}
Original Post URL: {content.post_url}
Author Agent: {content.author_agent}

Should this content be republished to the Telegram channel? Consider:
1. Content quality and relevance
2. Technical accuracy
3. Value to the channel audience
4. Brand and compliance alignment

Respond with ONLY "yes" or "no".
"""
        
        try:
            response = await litellm.acompletion(
                model=settings.DEEPSEEK_REASONING_MODEL,
                api_key=settings.DEEPSEEK_API_KEY,
                api_base=settings.DEEPSEEK_API_BASE,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=30
            )
            
            decision = response.choices[0].message.content.strip().lower()
            logger.info(f"DeepSeek evaluation for {content.id}: {decision}")
            return decision == "yes"
            
        except Exception as e:
            logger.error(f"DeepSeek evaluation failed: {e}")
            return True  # Default to publish if AI evaluation fails
    
    async def _publish_to_telegram(self, content: ContentItemModel) -> Dict[str, Any]:
        """Publish content to Telegram channel."""
        try:
            if not self.telegram_client:
                self.telegram_client = TelegramClient()
            
            # Create message with content and attribution
            message = f"""
📝 {content.title}

{content.body or str(content.variants)}

— Published by {content.author_agent}
Original: {content.post_url}
""".strip()
            
            result = await self.telegram_client.publish_post(
                text=message,
                post_id=content.post_id  # For idempotency
            )
            
            logger.info(f"Published to Telegram: {result.get('post_url')}")
            return result
            
        except Exception as e:
            logger.error(f"Telegram publishing failed: {e}")
            return {"error": str(e)}
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "auto_discover_seo_content": True,
            "republish_to_telegram": True,
            "ai_content_evaluation": True,
            "multi_agent_monitoring": True,
            "all_posts_digest": True
        }

    async def _build_all_posts_digest(self) -> Dict[str, Any]:
        """
        Build a digest of all published content from the last 6 hours across all agents/channels.
        """
        with get_sync_session() as session:
            # Get all published content from the last 6 hours
            cutoff = datetime.now() - timedelta(hours=6)

            all_content = session.query(ContentItemModel).filter(
                ContentItemModel.status == "published",
                ContentItemModel.published_at >= cutoff,
                ContentItemModel.post_url.isnot(None)
            ).order_by(desc(ContentItemModel.published_at)).all()

            if not all_content:
                return {
                    "outcome": "no_content",
                    "message": "No published content found in the last 6 hours"
                }

            # Build digest message
            digest_lines = [
                f"📊 Content Digest - Last 6 Hours ({cutoff.strftime('%Y-%m-%d %H:%M')} to {datetime.now().strftime('%Y-%m-%d %H:%M')})",
                f"Total posts: {len(all_content)}",
                ""
            ]

            for content in all_content:
                time_str = content.published_at.strftime('%Y-%m-%d %H:%M') if content.published_at else "Unknown"
                digest_lines.append(
                    f"📌 {content.title[:50]}{'...' if len(content.title) > 50 else ''}\n"
                    f"   Agent: {content.author_agent}\n"
                    f"   Channel: {content.channel}\n"
                    f"   Published: {time_str}\n"
                    f"   URL: {content.post_url}\n"
                )

            digest_message = "\n".join(digest_lines)

            # Post digest to Telegram
            try:
                if not self.telegram_client:
                    self.telegram_client = TelegramClient()

                result = await self.telegram_client.publish_post(
                    text=digest_message,
                    post_id=f"digest-{int(datetime.now().timestamp())}"  # Unique ID for idempotency
                )

                return {
                    "outcome": "digest_published",
                    "message": "All posts digest published",
                    "digest_url": result.get("post_url"),
                    "post_count": len(all_content)
                }

            except Exception as e:
                logger.error(f"Failed to publish digest: {e}")
                return {
                    "outcome": "digest_failed",
                    "error": str(e),
                    "post_count": len(all_content)
                }
