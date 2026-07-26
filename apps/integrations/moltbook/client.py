import httpx
import logging
import asyncio
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from apps.api.config import settings

logger = logging.getLogger(__name__)

class MoltbookClient:
    def __init__(
        self, 
        base_url: str = settings.MOLTBOOK_BASE_URL, 
        agent_key: str = settings.MOLTBOOK_AGENT_API_KEY, 
        app_key: str = settings.MOLTBOOK_APP_KEY, 
        timeout: float = 20
    ):
        self.base_url = base_url.rstrip("/")
        self.agent_key = agent_key
        self.app_key = app_key
        self.http = httpx.AsyncClient(timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def create_identity_token(self) -> Dict[str, Any]:
        """Confirmed in dev-guide."""
        r = await self.http.post(
            f"{self.base_url}/api/v1/agents/me/identity-token",
            headers={"Authorization": f"Bearer {self.agent_key}"},
        )
        r.raise_for_status()
        return r.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def verify_identity(self, token: str) -> Dict[str, Any]:
        """Confirmed in dev-guide."""
        r = await self.http.post(
            f"{self.base_url}/api/v1/agents/verify-identity",
            headers={"X-Moltbook-App-Key": self.app_key},
            json={"token": token},
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("success") or not data.get("valid"):
            raise ValueError("Invalid Moltbook identity token")
        return data["agent"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def publish_post(self, submolt: str, title: str, body: str) -> Dict[str, Any]:
        """
        Confirmed endpoint from live skill.md: POST /api/v1/posts
        Fields: submolt_name (or submolt), title, content
        """
        # Enforce dry-run if autopublish is disabled
        if not getattr(settings, "MOLTBOOK_AUTOPUBLISH", False):
            logger.info(f"[DRY-RUN] Publishing to {submolt}: {title}")
            return {
                "success": True,
                "dry_run": True,
                "post_id": "dry-run-id",
                "post_url": f"{self.base_url}/posts/dry-run-id"
            }

        payload = {
            "submolt_name": submolt,
            "title": title,
            "content": body
        }
        
        r = await self.http.post(
            f"{self.base_url}/api/v1/posts",
            headers={"Authorization": f"Bearer {self.agent_key}"},
            json=payload
        )
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
