"""
Credential service for managing per-agent platform credentials.
Provides agent-specific credential lookup with fallback to global settings.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.models.credential import CredentialModel
from apps.models.base import get_sync_session
from apps.api.config import settings

logger = logging.getLogger(__name__)


class CredentialService:
    """Service for retrieving agent-specific platform credentials."""
    
    @staticmethod
    async def get_agent_credentials(
        db: AsyncSession,
        agent_name: str,
        platform: str
    ) -> Optional[CredentialModel]:
        """
        Get credentials for a specific agent and platform (async).
        
        Args:
            db: Database session
            agent_name: Agent name (e.g., "Founder Content", "Technical Content")
            platform: Platform name (e.g., "x", "moltbook", "telegram")
        
        Returns:
            CredentialModel if found, None otherwise
        """
        result = await db.execute(
            select(CredentialModel).where(
                CredentialModel.agent_name == agent_name,
                CredentialModel.platform == platform
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_agent_credentials_sync(
        agent_name: str,
        platform: str
    ) -> Optional[CredentialModel]:
        """
        Get credentials for a specific agent and platform (sync).
        
        Args:
            agent_name: Agent name (e.g., "Founder Content", "Technical Content")
            platform: Platform name (e.g., "x", "moltbook", "telegram")
        
        Returns:
            CredentialModel if found, None otherwise
        """
        with get_sync_session() as session:
            result = session.execute(
                select(CredentialModel).where(
                    CredentialModel.agent_name == agent_name,
                    CredentialModel.platform == platform
                )
            )
            cred = result.scalar_one_or_none()
            if cred:
                # Eagerly load all columns to avoid session issues
                session.expunge(cred)
            return cred
    
    @staticmethod
    def get_x_credentials_sync(agent_name: str) -> Dict[str, Any]:
        """
        Get X/Twitter credentials for an agent (sync), with fallback to global settings.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with api_key, api_secret, access_token, access_token_secret, autopublish
        """
        # Try to get agent-specific credentials from database
        with get_sync_session() as session:
            result = session.execute(
                select(CredentialModel).where(
                    CredentialModel.agent_name == agent_name,
                    CredentialModel.platform == "x"
                )
            )
            cred = result.scalar_one_or_none()
            
            if cred and cred.x_api_key:
                return {
                    "api_key": cred.x_api_key,
                    "api_secret": cred.x_api_secret,
                    "access_token": cred.x_access_token,
                    "access_token_secret": cred.x_access_token_secret,
                    "autopublish": cred.x_autopublish
                }
        
        # Fallback to global settings
        return {
            "api_key": settings.X_API_KEY,
            "api_secret": settings.X_API_SECRET,
            "access_token": settings.X_ACCESS_TOKEN,
            "access_token_secret": settings.X_ACCESS_TOKEN_SECRET,
            "autopublish": getattr(settings, "X_AUTOPUBLISH", False)
        }
    
    @staticmethod
    def get_moltbook_credentials_sync(agent_name: str) -> Dict[str, Any]:
        """
        Get Moltbook credentials for an agent (sync), with fallback to global settings.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with agent_api_key, app_key, autopublish
        """
        # Try to get agent-specific credentials from database
        with get_sync_session() as session:
            result = session.execute(
                select(CredentialModel).where(
                    CredentialModel.agent_name == agent_name,
                    CredentialModel.platform == "moltbook"
                )
            )
            cred = result.scalar_one_or_none()
            
            if cred and cred.moltbook_agent_api_key:
                return {
                    "agent_api_key": cred.moltbook_agent_api_key,
                    "app_key": cred.moltbook_app_key,
                    "autopublish": cred.moltbook_autopublish
                }
        
        # Fallback to global settings
        return {
            "agent_api_key": settings.MOLTBOOK_AGENT_API_KEY,
            "app_key": settings.MOLTBOOK_APP_KEY,
            "autopublish": getattr(settings, "MOLTBOOK_AUTOPUBLISH", False)
        }
    
    @staticmethod
    def get_telegram_credentials_sync(agent_name: str) -> Dict[str, Any]:
        """
        Get Telegram credentials for an agent (sync), with fallback to global settings.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with bot_token, chat_id, default_channel, autopublish
        """
        # Try to get agent-specific credentials from database
        with get_sync_session() as session:
            result = session.execute(
                select(CredentialModel).where(
                    CredentialModel.agent_name == agent_name,
                    CredentialModel.platform == "telegram"
                )
            )
            cred = result.scalar_one_or_none()
            
            if cred and cred.telegram_bot_token:
                return {
                    "bot_token": cred.telegram_bot_token,
                    "chat_id": cred.telegram_chat_id,
                    "default_channel": cred.telegram_default_channel,
                    "autopublish": cred.telegram_autopublish
                }
        
        # Fallback to global settings
        return {
            "bot_token": settings.TELEGRAM_BOT_TOKEN,
            "chat_id": getattr(settings, "TELEGRAM_CHAT_ID", None),
            "default_channel": getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", None),
            "autopublish": getattr(settings, "TELEGRAM_AUTOPUBLISH", False)
        }
    
    @staticmethod
    async def get_x_credentials(db: AsyncSession, agent_name: str) -> Dict[str, Any]:
        """
        Get X/Twitter credentials for an agent (async), with fallback to global settings.
        
        Args:
            db: Database session
            agent_name: Agent name
        
        Returns:
            Dict with api_key, api_secret, access_token, access_token_secret, autopublish
        """
        # Try to get agent-specific credentials from database
        cred = await CredentialService.get_agent_credentials(db, agent_name, "x")
        
        if cred and cred.x_api_key:
            return {
                "api_key": cred.x_api_key,
                "api_secret": cred.x_api_secret,
                "access_token": cred.x_access_token,
                "access_token_secret": cred.x_access_token_secret,
                "autopublish": cred.x_autopublish
            }
        
        # Fallback to global settings
        return {
            "api_key": settings.X_API_KEY,
            "api_secret": settings.X_API_SECRET,
            "access_token": settings.X_ACCESS_TOKEN,
            "access_token_secret": settings.X_ACCESS_TOKEN_SECRET,
            "autopublish": getattr(settings, "X_AUTOPUBLISH", False)
        }
    
    @staticmethod
    async def get_moltbook_credentials(db: AsyncSession, agent_name: str) -> Dict[str, Any]:
        """
        Get Moltbook credentials for an agent (async), with fallback to global settings.
        
        Args:
            db: Database session
            agent_name: Agent name
        
        Returns:
            Dict with agent_api_key, app_key, autopublish
        """
        # Try to get agent-specific credentials from database
        cred = await CredentialService.get_agent_credentials(db, agent_name, "moltbook")
        
        if cred and cred.moltbook_agent_api_key:
            return {
                "agent_api_key": cred.moltbook_agent_api_key,
                "app_key": cred.moltbook_app_key,
                "autopublish": cred.moltbook_autopublish
            }
        
        # Fallback to global settings
        return {
            "agent_api_key": settings.MOLTBOOK_AGENT_API_KEY,
            "app_key": settings.MOLTBOOK_APP_KEY,
            "autopublish": getattr(settings, "MOLTBOOK_AUTOPUBLISH", False)
        }
    
    @staticmethod
    async def get_telegram_credentials(db: AsyncSession, agent_name: str) -> Dict[str, Any]:
        """
        Get Telegram credentials for an agent (async), with fallback to global settings.
        
        Args:
            db: Database session
            agent_name: Agent name
        
        Returns:
            Dict with bot_token, chat_id, default_channel, autopublish
        """
        # Try to get agent-specific credentials from database
        cred = await CredentialService.get_agent_credentials(db, agent_name, "telegram")
        
        if cred and cred.telegram_bot_token:
            return {
                "bot_token": cred.telegram_bot_token,
                "chat_id": cred.telegram_chat_id,
                "default_channel": cred.telegram_default_channel,
                "autopublish": cred.telegram_autopublish
            }
        
        # Fallback to global settings
        return {
            "bot_token": settings.TELEGRAM_BOT_TOKEN,
            "chat_id": getattr(settings, "TELEGRAM_CHAT_ID", None),
            "default_channel": getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", None),
            "autopublish": getattr(settings, "TELEGRAM_AUTOPUBLISH", False)
        }
