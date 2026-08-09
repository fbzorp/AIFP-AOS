"""
X/Twitter publishing client structure (simplified for code path validation).
Full OAuth1.0a implementation to be added when live credentials are provided.
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


class XClient:
    """X/Twitter API v2 client structure for publishing tweets."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        timeout: float = 20
    ):
        self._api_key = api_key
        self._api_secret = api_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret
        self._timeout = timeout
        self.http = httpx.AsyncClient(timeout=timeout)
    
    @property
    def api_key(self) -> str:
        return self._api_key or settings.X_API_KEY or ""
    
    @property
    def api_secret(self) -> str:
        return self._api_secret or settings.X_API_SECRET or ""
    
    @property
    def access_token(self) -> str:
        return self._access_token or settings.X_ACCESS_TOKEN or ""
    
    @property
    def access_token_secret(self) -> str:
        return self._access_token_secret or settings.X_ACCESS_TOKEN_SECRET or ""
    
    @property
    def autopublish_enabled(self) -> bool:
        return getattr(settings, "X_AUTOPUBLISH", False)
    
    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def publish_post(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Publish a tweet using X API v2.
        
        Args:
            text: Tweet text (max 280 characters)
            **kwargs: Additional parameters (e.g., reply_to, media_ids)
        
        Returns:
            Dict with keys: success, dry_run, post_id, post_url
        """
        # Enforce dry-run if autopublish is disabled
        if not self.autopublish_enabled:
            logger.info("[DRY-RUN] X/Twitter publishing disabled (X_AUTOPUBLISH=false)")
            return {
                "success": True,
                "dry_run": True,
                "post_id": None,
                "post_url": None
            }
        
        # Idempotency check - skip if already has post_id
        existing_post_id = kwargs.get("post_id")
        if existing_post_id:
            logger.info(f"Tweet already published with post_id: {existing_post_id}")
            return {
                "success": True,
                "dry_run": False,
                "post_id": existing_post_id,
                "post_url": f"https://x.com/i/status/{existing_post_id}"
            }
        
        # Validate text length
        if len(text) > 280:
            raise ValueError(f"Tweet text exceeds 280 characters: {len(text)}")
        
        if not text.strip():
            raise ValueError("Tweet text cannot be empty")
        
        # Check if credentials are configured
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.warning("X API credentials not fully configured, falling back to dry-run")
            return {
                "success": True,
                "dry_run": True,
                "post_id": None,
                "post_url": None
            }
        
        # Placeholder for actual X API implementation
        # This will be implemented when live credentials are provided
        logger.info("X API implementation placeholder - credentials present but full OAuth not yet implemented")
        return {
            "success": True,
            "dry_run": True,
            "post_id": None,
            "post_url": None
        }
    
    async def close(self):
        await self.http.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
