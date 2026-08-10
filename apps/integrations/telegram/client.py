"""
Telegram Bot API client for publishing messages to channels.
Real implementation using Telegram Bot API.
"""

import httpx
import logging
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from apps.api.config import settings

logger = logging.getLogger(__name__)


def is_transient_error(exception: Exception) -> bool:
    """Returns True for transient network/server errors that should be retried."""
    if isinstance(exception, (httpx.TransportError, httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry only on 5xx (Server Error) or 429 (Too Many Requests)
        return exception.response.status_code >= 500 or exception.response.status_code == 429
    return False


class TelegramClient:
    """Telegram Bot API client for publishing messages."""
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        autopublish: Optional[bool] = None,
        timeout: float = 20
    ):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._autopublish = autopublish
        self._timeout = timeout
        self.http = httpx.AsyncClient(timeout=timeout)
    
    @property
    def bot_token(self) -> str:
        return self._bot_token or settings.TELEGRAM_BOT_TOKEN or ""
    
    @property
    def chat_id(self) -> str:
        return self._chat_id or getattr(settings, "TELEGRAM_CHAT_ID", "") or getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", "")
    
    @property
    def default_channel(self) -> str:
        return getattr(settings, "TELEGRAM_DEFAULT_CHANNEL", "")
    
    @property
    def autopublish_enabled(self) -> bool:
        if self._autopublish is not None:
            return self._autopublish
        return getattr(settings, "TELEGRAM_AUTOPUBLISH", False)
    
    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def publish_post(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Publish a message to Telegram channel/chat.
        
        Args:
            text: Message text
            **kwargs: Additional parameters (e.g., parse_mode, disable_notification)
        
        Returns:
            Dict with keys: success, dry_run, post_id, post_url
        """
        # Enforce dry-run if autopublish is disabled
        if not self.autopublish_enabled:
            logger.info("[DRY-RUN] Telegram publishing disabled (TELEGRAM_AUTOPUBLISH=false)")
            return {
                "success": True,
                "dry_run": True,
                "post_id": None,
                "post_url": None
            }
        
        # Idempotency check - skip if already has post_id
        existing_post_id = kwargs.get("post_id")
        if existing_post_id:
            logger.info(f"Message already published with post_id: {existing_post_id}")
            channel = self.chat_id or "unknown"
            return {
                "success": True,
                "dry_run": False,
                "post_id": existing_post_id,
                "post_url": f"https://t.me/{channel}/{existing_post_id}"
            }
        
        # Validate text
        if not text.strip():
            raise ValueError("Message text cannot be empty")
        
        # Check if credentials are configured
        if not self.bot_token:
            logger.warning("Telegram bot token not configured, falling back to dry-run")
            return {
                "success": True,
                "dry_run": True,
                "post_id": None,
                "post_url": None
            }
        
        if not self.chat_id:
            logger.warning("Telegram chat_id not configured, falling back to dry-run")
            return {
                "success": True,
                "dry_run": True,
                "post_id": None,
                "post_url": None
            }
        
        # Telegram Bot API sendMessage endpoint
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": kwargs.get("parse_mode", "HTML")
        }
        
        try:
            response = await self.http.post(url, json=payload)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                logger.warning(f"Telegram API rate limit hit. Retry-after: {retry_after}")
                raise httpx.HTTPStatusError(
                    "Rate limit exceeded",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract message ID and construct URL
            message_id = data.get("result", {}).get("message_id")
            if not message_id:
                raise ValueError("Telegram API response missing message_id")
            
            # Construct public URL if channel is public
            channel = self.default_channel or self.chat_id
            post_url = f"https://t.me/{channel}/{message_id}" if channel.startswith("@") else f"https://t.me/c/{channel}/{message_id}"
            
            logger.info(f"Successfully published to Telegram: {post_url}")
            
            return {
                "success": True,
                "dry_run": False,
                "post_id": str(message_id),
                "post_url": post_url
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Telegram API request failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Telegram client error: {e}")
            raise
    
    async def close(self):
        await self.http.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
