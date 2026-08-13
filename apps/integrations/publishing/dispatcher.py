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
                "app_key": settings.MOLTBOOK_APP_KEY
            }

        self._client = MoltbookClient(
            agent_key=creds.get("agent_api_key"),
            app_key=creds.get("app_key"),
            timeout=20
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
                "access_token_secret": settings.X_ACCESS_TOKEN_SECRET
            }

        self._client = XClient(
            api_key=creds.get("api_key"),
            api_secret=creds.get("api_secret"),
            access_token=creds.get("access_token"),
            access_token_secret=creds.get("access_token_secret"),
            timeout=20
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
                "default_channel": getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", None)
            }

        self._client = TelegramClient(
            bot_token=creds.get("bot_token"),
            chat_id=creds.get("chat_id"),
            timeout=20
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


class MultiChannelPublisher(PublisherBase):
    """
    Multi-channel publisher that fans out content to multiple platforms.
    Used for SEO/Google content to maximize reach across available channels.
    """

    def __init__(self, agent_name: Optional[str] = None):
        self._agent_name = agent_name
        self._publishers: Dict[str, PublisherBase] = {}
        self._initialized = False

    def _ensure_initialized(self):
        """Initialize all available publishers for the agent."""
        if self._initialized:
            return

        # Initialize all available publishers with agent-specific credentials
        # We'll publish to Moltbook, X, and Telegram if credentials are available
        channels_to_try = ["moltbook", "x", "telegram"]

        for channel in channels_to_try:
            try:
                publisher = get_publisher(channel, self._agent_name)
                self._publishers[channel] = publisher
                logger.info(f"MultiChannelPublisher: Initialized {channel} publisher for agent {self._agent_name}")
            except Exception as e:
                logger.warning(f"MultiChannelPublisher: Could not initialize {channel} publisher: {e}")

        if not self._publishers:
            logger.warning(f"MultiChannelPublisher: No publishers initialized for agent {self._agent_name}")

        self._initialized = True

    async def publish_post(self, title: str, body: str, **kwargs) -> Dict:
        """
        Publish to all available channels.
        Returns the first successful result, or aggregate error info.
        """
        self._ensure_initialized()

        if not self._publishers:
            return {
                "success": False,
                "dry_run": True,
                "post_id": None,
                "post_url": None,
                "error": "No publishers available"
            }

        results = []
        last_successful_result = None

        for channel, publisher in self._publishers.items():
            try:
                result = await publisher.publish_post(title, body, **kwargs)
                results.append((channel, result))

                if result.get("success") and result.get("post_url"):
                    last_successful_result = result
                    logger.info(f"MultiChannelPublisher: Successfully published to {channel}: {result.get('post_url')}")
                else:
                    logger.warning(f"MultiChannelPublisher: Failed to publish to {channel}: {result}")

            except Exception as e:
                logger.error(f"MultiChannelPublisher: Error publishing to {channel}: {e}")
                results.append((channel, {"success": False, "error": str(e)}))

        # Return the last successful result (prioritizing channels in order)
        if last_successful_result:
            return last_successful_result

        # If no success, return error info
        return {
            "success": False,
            "dry_run": True,
            "post_id": None,
            "post_url": None,
            "error": f"All publishers failed. Results: {results}"
        }

    async def close(self):
        """Close all publishers."""
        for publisher in self._publishers.values():
            await publisher.close()


# Channel to publisher mapping
_CHANNEL_PUBLISHERS: Dict[str, Type[PublisherBase]] = {
    "moltbook": MoltbookPublisher,
    "general": MoltbookPublisher,  # Moltbook submolt
    "aifintech": MoltbookPublisher,  # Moltbook submolt
    "aiagents": MoltbookPublisher,  # Moltbook submolt
    "x": XPublisher,
    "twitter": XPublisher,
    "telegram": TelegramPublisher,
    # SEO/Google/Blog channels map to multi-channel publisher for maximum reach
    "google": MultiChannelPublisher,
    "seo": MultiChannelPublisher,
    "blog": MultiChannelPublisher,
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
