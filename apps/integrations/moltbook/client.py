import httpx
import logging
import asyncio
from typing import Any, Dict, List, Optional
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
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

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=8),
    )
    async def discover_discussions(
        self,
        query: str,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Discover relevant Moltbook posts through the read-only semantic search API.

        The returned records use the Community Engagement Agent's normalized
        discussion shape and do not create comments, votes, or posts.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Moltbook discovery query must be a non-empty string")
        if len(query) > 500:
            raise ValueError("Moltbook discovery query must contain at most 500 characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise ValueError("Moltbook discovery limit must be an integer from 1 to 50")
        if cursor is not None and (not isinstance(cursor, str) or not cursor.strip()):
            raise ValueError("Moltbook discovery cursor must be a non-empty string when provided")

        params: Dict[str, Any] = {
            "q": query.strip(),
            "type": "posts",
            "limit": limit,
        }
        if cursor is not None:
            params["cursor"] = cursor

        response = await self.http.get(
            f"{self.base_url}/api/v1/search",
            headers={"Authorization": f"Bearer {self.agent_key}"},
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success", False):
            raise ValueError("Moltbook discussion search was unsuccessful")

        results = data.get("results", [])
        if not isinstance(results, list):
            raise ValueError("Moltbook discussion search returned an invalid results payload")

        discussions: List[Dict[str, Any]] = []
        for result in results:
            if not isinstance(result, dict) or result.get("type") != "post":
                continue

            post_id = result.get("post_id") or result.get("id")
            submolt = result.get("submolt") or {}
            submolt_name = submolt.get("name") if isinstance(submolt, dict) else None
            content = result.get("content")
            title = result.get("title")
            if not isinstance(post_id, str) or not post_id:
                continue
            if not isinstance(submolt_name, str) or not submolt_name:
                continue
            if not isinstance(content, str) or not content.strip():
                continue

            discussion_text = content.strip()
            if isinstance(title, str) and title.strip():
                discussion_text = f"{title.strip()}\n\n{discussion_text}"

            discussions.append(
                {
                    "url": f"{self.base_url}/posts/{post_id}",
                    "post_id": post_id,
                    "submolt": submolt_name,
                    "content": discussion_text,
                    "author": (result.get("author") or {}).get("name"),
                    "similarity": result.get("similarity"),
                }
            )

        return discussions

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=8),
    )
    async def list_discussions(
        self,
        submolt: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """List recent posts from one Moltbook submolt without sanitizing them.

        The live Moltbook skill documents this read-only endpoint as
        ``GET /api/v1/posts?submolt=<name>&sort=new``. Callers are responsible
        for treating the returned content as external, untrusted data.
        """
        if not isinstance(submolt, str) or not submolt.strip():
            raise ValueError("Moltbook submolt must be a non-empty string")
        if len(submolt.strip()) > 100:
            raise ValueError("Moltbook submolt must contain at most 100 characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise ValueError("Moltbook discussion limit must be an integer from 1 to 50")

        normalized_submolt = submolt.strip()
        response = await self.http.get(
            f"{self.base_url}/api/v1/posts",
            headers={"Authorization": f"Bearer {self.agent_key}"},
            params={
                "submolt": normalized_submolt,
                "sort": "new",
                "limit": limit,
            },
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            posts = data
        elif isinstance(data, dict):
            if data.get("success") is False:
                raise ValueError("Moltbook discussion listing was unsuccessful")
            posts = data.get("posts")
            if posts is None:
                nested_data = data.get("data")
                if isinstance(nested_data, dict):
                    posts = nested_data.get("posts")
                elif isinstance(nested_data, list):
                    posts = nested_data
        else:
            posts = None

        if not isinstance(posts, list):
            raise ValueError("Moltbook discussion listing returned an invalid posts payload")

        discussions: List[Dict[str, str]] = []
        for post in posts:
            if not isinstance(post, dict):
                continue

            post_id = post.get("post_id") or post.get("id")
            post_submolt = post.get("submolt")
            if isinstance(post_submolt, dict):
                post_submolt = post_submolt.get("name")
            post_submolt = post.get("submolt_name") or post_submolt or normalized_submolt
            content = post.get("content")

            if not isinstance(post_id, str) or not post_id:
                continue
            if not isinstance(post_submolt, str) or not post_submolt.strip():
                continue
            if not isinstance(content, str) or not content.strip():
                continue

            discussions.append(
                {
                    "url": f"{self.base_url}/posts/{post_id}",
                    "submolt": post_submolt.strip(),
                    "content": content,
                }
            )

        return discussions

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
