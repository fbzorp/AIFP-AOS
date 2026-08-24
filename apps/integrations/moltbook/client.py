import httpx
import logging
import asyncio
from typing import Any, Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from apps.api.config import settings
import litellm

logger = logging.getLogger(__name__)

def is_transient_error(exception: Exception) -> bool:
    """Returns True for transient network/server errors that should be retried."""
    if isinstance(exception, (httpx.TransportError, httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry only on 5xx (Server Error) or 429 (Too Many Requests)
        return exception.response.status_code >= 500 or exception.response.status_code == 429
    return False

class MoltbookClient:
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        agent_key: Optional[str] = None, 
        app_key: Optional[str] = None, 
        timeout: float = 20
    ):
        self._base_url = base_url
        self._agent_key = agent_key
        self._app_key = app_key
        self.http = httpx.AsyncClient(timeout=timeout)

    @property
    def base_url(self) -> str:
        return (self._base_url or settings.MOLTBOOK_BASE_URL).rstrip("/")

    @property
    def agent_key(self) -> str:
        return self._agent_key or settings.MOLTBOOK_AGENT_API_KEY or ""

    @property
    def app_key(self) -> str:
        return self._app_key or settings.MOLTBOOK_APP_KEY or ""

    @property
    def autopublish_enabled(self) -> bool:
        return getattr(settings, "MOLTBOOK_AUTOPUBLISH", False)


    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def create_identity_token(self) -> Dict[str, Any]:
        """Confirmed in dev-guide."""
        r = await self.http.post(
            f"{self.base_url}/api/v1/agents/me/identity-token",
            headers={"Authorization": f"Bearer {self.agent_key}"},
        )
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Moltbook identity token creation failed: {e.response.status_code} - {e.response.text}")
            raise
        return r.json()

    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def verify_identity(self, token: str) -> Dict[str, Any]:
        """Confirmed in dev-guide."""
        r = await self.http.post(
            f"{self.base_url}/api/v1/agents/verify-identity",
            headers={"X-Moltbook-App-Key": self.app_key},
            json={"token": token},
        )
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Moltbook identity verification failed: {e.response.status_code} - {e.response.text}")
            raise
        data = r.json()
        if not data.get("success") or not data.get("valid"):
            raise ValueError("Invalid Moltbook identity token")
        return data["agent"]

    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
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

    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def verify_challenge(self, verification_code: str, answer: str) -> Dict[str, Any]:
        """Submit answer to a verification challenge."""
        r = await self.http.post(
            f"{self.base_url}/api/v1/verify",
            headers={"Authorization": f"Bearer {self.agent_key}"},
            json={"verification_code": verification_code, "answer": answer},
        )
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Moltbook verification challenge failed: {e.response.status_code} - {e.response.text}")
            raise
        return r.json()

    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def publish_post(self, submolt: str, title: str, body: str, identity_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Confirmed endpoint from live skill.md: POST /api/v1/posts
        Authorization: Bearer <AGENT_KEY> (per skill.md)
        Fields: submolt_name (or submolt), title, content
        
        Returns:
            Dict with keys: success, dry_run, post_id, post_url
        """
        # Check if credentials are configured
        if not self.agent_key:
            logger.error("Moltbook agent key not configured")
            return {
                "success": False,
                "post_id": None,
                "post_url": None,
                "error": "Moltbook agent key not configured"
            }

        payload = {
            "submolt_name": submolt,
            "title": title,
            "content": body
        }
        
        # Per skill.md, all requests after registration require your API key.
        # Dev-guide also notes identity token is for target backends, not Moltbook itself.
        headers = {"Authorization": f"Bearer {self.agent_key}"}
        
        try:
            r = await self.http.post(
                f"{self.base_url}/api/v1/posts",
                headers=headers,
                json=payload
            )
            
            r.raise_for_status()
            data = r.json()
            
            # Handle verification if required
            if data.get("verification_required") or (isinstance(data.get("post"), dict) and data["post"].get("verification")):
                post_data = data.get("post") or {}
                verification = post_data.get("verification") or {}
                code = verification.get("verification_code")
                challenge = verification.get("challenge_text")
                
                if code and challenge:
                    logger.info(f"Verification required for post. Challenge: {challenge}")
                    # We need an LLM to solve the obfuscated math problem

                    if not settings.DEEPSEEK_API_KEY:
                        logger.error("DEEPSEEK_API_KEY not found - cannot solve challenge")
                        return {
                            "success": False,
                            "post_id": None,
                            "post_url": None,
                            "error": "DEEPSEEK_API_KEY not found for verification"
                        }

                    prompt = f"Solve this Moltbook AI verification challenge. It is an obfuscated math problem. Extract the two numbers and the operation, compute the result, and respond with ONLY the number (e.g., '15.00').\n\nChallenge: {challenge}"
                    
                    try:
                        llm_response = await litellm.acompletion(
                            model=settings.DEEPSEEK_PRIMARY_MODEL,
                            api_key=settings.DEEPSEEK_API_KEY,
                            api_base=settings.DEEPSEEK_API_BASE,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            timeout=30
                        )
                        answer = llm_response.choices[0].message.content.strip()
                    except Exception as e:
                        logger.error(f"LiteLLM completion failed for verification challenge: {e}")
                        return {
                            "success": False,
                            "post_id": None,
                            "post_url": None,
                            "error": f"LLM verification failed: {str(e)}"
                        }

                    
                    logger.info(f"Submitting verification answer: {answer}")
                    verify_result = await self.verify_challenge(code, answer)
                    if verify_result.get("success"):
                        logger.info("Verification successful!")
                        # Merge verification success into original response
                        post_id = post_data.get("id")
                        # Use API URL instead of web URL since web URLs return 404 for agent posts
                        post_url = f"{self.base_url}/api/v1/posts/{post_id}"
                        return {
                            "success": True,
                            "post_id": post_id,
                            "post_url": post_url
                        }
                    else:
                        logger.error(f"Verification failed: {verify_result.get('error')}")
                        return {
                            "success": False,
                            "post_id": None,
                            "post_url": None,
                            "error": f"Verification failed: {verify_result.get('error')}"
                        }
            else:
                # Normal success path
                post_data = data.get("post") or data.get("agent") or {}
                post_id = data.get("post_id") or post_data.get("id")
                # Use API URL instead of web URL since web URLs return 404 for agent posts
                post_url = data.get("post_url") or f"{self.base_url}/api/v1/posts/{post_id}"
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": post_url
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Moltbook publish_post failed: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "post_id": None,
                "post_url": None,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Moltbook client error: {e}")
            return {
                "success": False,
                "post_id": None,
                "post_url": None,
                "error": str(e)
            }

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
