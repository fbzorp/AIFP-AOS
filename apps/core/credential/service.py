"""
Credential service for managing per-agent platform credentials.
Single source of truth: .env file with agent-specific credential sections.
"""

import logging
from typing import Dict, Any
from apps.api.config import settings

logger = logging.getLogger(__name__)


class CredentialService:
    """Service for retrieving agent-specific platform credentials from .env (single source of truth)."""
    
    @staticmethod
    def get_x_credentials_sync(agent_name: str) -> Dict[str, Any]:
        """
        Get X/Twitter credentials for an agent directly from .env.
        
        Args:
            agent_name: Agent name (e.g., "Founder Content", "Technical Content", "SEO Content")
        
        Returns:
            Dict with api_key, api_secret, access_token, access_token_secret, autopublish
        """
        # Convert agent name to environment variable prefix
        agent_prefix = agent_name.upper().replace(" ", "_")
        
        # Try agent-specific credentials first
        agent_api_key = getattr(settings, f"{agent_prefix}_X_API_KEY", None)
        agent_api_secret = getattr(settings, f"{agent_prefix}_X_API_SECRET", None)
        agent_access_token = getattr(settings, f"{agent_prefix}_X_ACCESS_TOKEN", None)
        agent_access_token_secret = getattr(settings, f"{agent_prefix}_X_ACCESS_TOKEN_SECRET", None)
        agent_autopublish = getattr(settings, f"{agent_prefix}_X_AUTOPUBLISH", None)
        
        if agent_api_key and agent_api_secret and agent_access_token and agent_access_token_secret:
            logger.info(f"Using agent-specific X credentials for {agent_name}")
            return {
                "api_key": agent_api_key,
                "api_secret": agent_api_secret,
                "access_token": agent_access_token,
                "access_token_secret": agent_access_token_secret
            }

        # Fallback to global credentials
        logger.info(f"Using global X credentials for {agent_name}")
        return {
            "api_key": settings.X_API_KEY,
            "api_secret": settings.X_API_SECRET,
            "access_token": settings.X_ACCESS_TOKEN,
            "access_token_secret": settings.X_ACCESS_TOKEN_SECRET
        }
    
    @staticmethod
    def get_moltbook_credentials_sync(agent_name: str) -> Dict[str, Any]:
        """
        Get Moltbook credentials for an agent directly from .env.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with agent_api_key, app_key, autopublish
        """
        # Convert agent name to environment variable prefix
        agent_prefix = agent_name.upper().replace(" ", "_")
        
        # Try agent-specific credentials first
        agent_api_key = getattr(settings, f"{agent_prefix}_MOLTBOOK_AGENT_API_KEY", None)
        agent_app_key = getattr(settings, f"{agent_prefix}_MOLTBOOK_APP_KEY", None)
        agent_autopublish = getattr(settings, f"{agent_prefix}_MOLTBOOK_AUTOPUBLISH", None)
        
        if agent_api_key:
            logger.info(f"Using agent-specific Moltbook credentials for {agent_name}")
            return {
                "agent_api_key": agent_api_key,
                "app_key": agent_app_key or ""  # Empty string is fine for Moltbook posting
            }

        # Fallback to global credentials
        logger.info(f"Using global Moltbook credentials for {agent_name}")
        return {
            "agent_api_key": settings.MOLTBOOK_AGENT_API_KEY,
            "app_key": settings.MOLTBOOK_APP_KEY or ""  # Empty string is fine for Moltbook posting
        }
    
    @staticmethod
    def get_telegram_credentials_sync(agent_name: str) -> Dict[str, Any]:
        """
        Get Telegram credentials for an agent directly from .env.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with bot_token, chat_id, default_channel, autopublish
        """
        # Convert agent name to environment variable prefix
        agent_prefix = agent_name.upper().replace(" ", "_")
        
        # Try agent-specific credentials first
        agent_bot_token = getattr(settings, f"{agent_prefix}_TELEGRAM_BOT_TOKEN", None)
        agent_chat_id = getattr(settings, f"{agent_prefix}_TELEGRAM_CHAT_ID", None)
        agent_default_channel = getattr(settings, f"{agent_prefix}_TELEGRAM_DEFAULT_CHANNEL", None)
        agent_autopublish = getattr(settings, f"{agent_prefix}_TELEGRAM_AUTOPUBLISH", None)
        
        if agent_bot_token:
            logger.info(f"Using agent-specific Telegram credentials for {agent_name}")
            return {
                "bot_token": agent_bot_token,
                "chat_id": agent_chat_id,
                "default_channel": agent_default_channel
            }

        # Fallback to global credentials
        logger.info(f"Using global Telegram credentials for {agent_name}")
        return {
            "bot_token": settings.TELEGRAM_BOT_TOKEN,
            "chat_id": getattr(settings, "TELEGRAM_CHAT_ID", None),
            "default_channel": getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", None)
        }
    
    @staticmethod
    async def get_x_credentials(agent_name: str) -> Dict[str, Any]:
        """
        Get X/Twitter credentials for an agent (async wrapper).
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with api_key, api_secret, access_token, access_token_secret, autopublish
        """
        return CredentialService.get_x_credentials_sync(agent_name)
    
    @staticmethod
    async def get_moltbook_credentials(agent_name: str) -> Dict[str, Any]:
        """
        Get Moltbook credentials for an agent (async wrapper).
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with agent_api_key, app_key, autopublish
        """
        return CredentialService.get_moltbook_credentials_sync(agent_name)
    
    @staticmethod
    async def get_telegram_credentials(agent_name: str) -> Dict[str, Any]:
        """
        Get Telegram credentials for an agent (async wrapper).
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with bot_token, chat_id, default_channel, autopublish
        """
        return CredentialService.get_telegram_credentials_sync(agent_name)
