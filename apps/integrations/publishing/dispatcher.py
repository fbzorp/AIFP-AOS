"""
Channel-agnostic publisher dispatcher.
Maps content.channel to the appropriate publishing client.
"""

import logging
from typing import Dict, Type, Optional
from abc import ABC, abstractmethod
from apps.api.config import settings

logger = logging.getLogger(__name__)


class PublisherBase(ABC):
    """Base class for all publishing clients."""
    
    @abstractmethod
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """
        Publish content to the platform.
        
        Returns normalized dict with keys:
        - success: bool
        - dry_run: bool
        - post_id: Optional[str]
        - post_url: Optional[str]
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Clean up resources."""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class MoltbookPublisher(PublisherBase):
    """Moltbook publishing client wrapper."""
    
    def __init__(self):
        from apps.integrations.moltbook.client import MoltbookClient
        self._client = MoltbookClient()
    
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """Publish to Moltbook with channel-specific submolt."""
        submolt = kwargs.get("submolt", "general")
        
        # Enforce allowlist
        allowed_submolts = getattr(settings, "MOLTBOOK_ALLOWED_SUBMOLTS", "general").split(",")
        target_submolt = submolt.lower()
        if target_submolt not in [s.strip().lower() for s in allowed_submolts]:
            raise ValueError(f"Submolt {target_submolt} not in allowlist")
        
        result = await self._client.publish_post(
            submolt=target_submolt,
            title=title,
            body=body
        )
        
        return {
            "success": True,
            "dry_run": result.get("dry_run", False),
            "post_id": result.get("post_id"),
            "post_url": result.get("post_url")
        }
    
    async def close(self):
        await self._client.close()


class XPublisher(PublisherBase):
    """X/Twitter publishing client."""
    
    def __init__(self):
        from apps.integrations.x.client import XClient
        self._client = XClient()
    
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """Publish to X/Twitter."""
        result = await self._client.publish_post(
            text=body,  # X uses text, not title/body
            **kwargs
        )
        
        return {
            "success": result.get("success", False),
            "dry_run": result.get("dry_run", False),
            "post_id": result.get("post_id"),
            "post_url": result.get("post_url")
        }
    
    async def close(self):
        await self._client.close()


class TelegramPublisher(PublisherBase):
    """Telegram publishing client."""
    
    def __init__(self):
        from apps.integrations.telegram.client import TelegramClient
        self._client = TelegramClient()
    
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """Publish to Telegram."""
        # Combine title and body for Telegram
        text = f"{title}\n\n{body}" if title else body
        
        result = await self._client.publish_post(
            text=text,
            **kwargs
        )
        
        return {
            "success": result.get("success", False),
            "dry_run": result.get("dry_run", False),
            "post_id": result.get("post_id"),
            "post_url": result.get("post_url")
        }
    
    async def close(self):
        await self._client.close()


# Channel to publisher mapping
_CHANNEL_PUBLISHERS: Dict[str, Type[PublisherBase]] = {
    "moltbook": MoltbookPublisher,
    "general": MoltbookPublisher,  # Moltbook submolt
    "aifintech": MoltbookPublisher,  # Moltbook submolt
    "aiagents": MoltbookPublisher,  # Moltbook submolt
    "x": XPublisher,
    "twitter": XPublisher,
    "telegram": TelegramPublisher,
}


def get_publisher(channel: str) -> PublisherBase:
    """
    Get the appropriate publisher client for a given channel.
    
    Args:
        channel: The content channel (e.g., "moltbook", "x", "telegram")
    
    Returns:
        PublisherBase instance for the channel
    
    Raises:
        ValueError: If channel is not supported
    """
    normalized_channel = channel.lower().strip()
    
    publisher_class = _CHANNEL_PUBLISHERS.get(normalized_channel)
    if not publisher_class:
        raise ValueError(f"Unsupported channel: {channel}. Supported channels: {list(_CHANNEL_PUBLISHERS.keys())}")
    
    logger.info(f"Resolved publisher for channel '{channel}' to {publisher_class.__name__}")
    return publisher_class()
