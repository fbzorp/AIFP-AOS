"""
Channel-agnostic publisher dispatcher.
Maps content.channel to the appropriate publishing client.
"""

import logging
from typing import Dict, Type, Optional, Any
from abc import ABC, abstractmethod
from apps.api.config import settings
from apps.integrations.moltbook.client import MoltbookClient
from apps.integrations.x.client import XClient
from apps.integrations.telegram.client import TelegramClient

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
    
    def __init__(self, agent_name: Optional[str] = None):
        self._agent_name = agent_name
        self._client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization with agent-specific credential lookup."""
        if self._initialized:
            return
        
        from apps.core.credential import CredentialService
        
        # Get agent-specific credentials (sync for dramatiq workers)
        if self._agent_name:
            creds = CredentialService.get_moltbook_credentials_sync(self._agent_name)
        else:
            # Fallback to global settings
            creds = {
                "agent_api_key": settings.MOLTBOOK_AGENT_API_KEY,
                "app_key": settings.MOLTBOOK_APP_KEY,
                "autopublish": getattr(settings, "MOLTBOOK_AUTOPUBLISH", False)
            }
        
        self._client = MoltbookClient(
            agent_api_key=creds.get("agent_api_key"),
            app_key=creds.get("app_key"),
            autopublish=creds.get("autopublish")
        )
        self._initialized = True
    
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """Publish to Moltbook with channel-specific submolt."""
        self._ensure_initialized()
        
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
        if self._client:
            await self._client.close()


class XPublisher(PublisherBase):
    """X/Twitter publishing client."""
    
    def __init__(self, agent_name: Optional[str] = None):
        from apps.core.credential import CredentialService
        
        self._agent_name = agent_name
        self._client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization with sync credential lookup."""
        if self._initialized:
            return
        
        from apps.core.credential import CredentialService
        
        # Get agent-specific credentials (sync for dramatiq workers)
        if self._agent_name:
            creds = CredentialService.get_x_credentials_sync(self._agent_name)
        else:
            # Fallback to global settings
            creds = {
                "api_key": settings.X_API_KEY,
                "api_secret": settings.X_API_SECRET,
                "access_token": settings.X_ACCESS_TOKEN,
                "access_token_secret": settings.X_ACCESS_TOKEN_SECRET,
                "autopublish": getattr(settings, "X_AUTOPUBLISH", False)
            }
        
        self._client = XClient(
            api_key=creds.get("api_key"),
            api_secret=creds.get("api_secret"),
            access_token=creds.get("access_token"),
            access_token_secret=creds.get("access_token_secret"),
            autopublish=creds.get("autopublish")
        )
        self._initialized = True
    
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """Publish to X/Twitter."""
        self._ensure_initialized()
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
        if self._client:
            await self._client.close()


class TelegramPublisher(PublisherBase):
    """Telegram publishing client."""
    
    def __init__(self, agent_name: Optional[str] = None):
        from apps.core.credential import CredentialService
        
        self._agent_name = agent_name
        self._client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization with sync credential lookup."""
        if self._initialized:
            return
        
        from apps.core.credential import CredentialService
        
        # Get agent-specific credentials (sync for dramatiq workers)
        if self._agent_name:
            creds = CredentialService.get_telegram_credentials_sync(self._agent_name)
        else:
            # Fallback to global settings
            creds = {
                "bot_token": settings.TELEGRAM_BOT_TOKEN,
                "chat_id": getattr(settings, "TELEGRAM_CHAT_ID", None),
                "default_channel": getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", None),
                "autopublish": getattr(settings, "TELEGRAM_AUTOPUBLISH", False)
            }
        
        self._client = TelegramClient(
            bot_token=creds.get("bot_token"),
            chat_id=creds.get("chat_id"),
            autopublish=creds.get("autopublish")
        )
        self._initialized = True
    
    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """Publish to Telegram."""
        self._ensure_initialized()
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
        if self._client:
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


def get_publisher(channel: str, agent_name: Optional[str] = None) -> PublisherBase:
    """
    Get the appropriate publisher client for a given channel and agent.
    
    Args:
        channel: The content channel (e.g., "moltbook", "x", "telegram")
        agent_name: The agent name for credential lookup (e.g., "Founder Content")
    
    Returns:
        PublisherBase instance for the channel
    
    Raises:
        ValueError: If channel is not supported
    """
    normalized_channel = channel.lower().strip()
    
    publisher_class = _CHANNEL_PUBLISHERS.get(normalized_channel)
    if not publisher_class:
        raise ValueError(f"Unsupported channel: {channel}. Supported channels: {list(_CHANNEL_PUBLISHERS.keys())}")
    
    logger.info(f"Resolved publisher for channel '{channel}' and agent '{agent_name}' to {publisher_class.__name__}")
    return publisher_class(agent_name=agent_name)
