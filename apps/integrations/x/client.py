"""
X/Twitter publishing client using OAuth1.0a and API v2.
Real implementation for publishing tweets.
"""

import httpx
import logging
import base64
import hashlib
import hmac
import urllib.parse
import time
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
    """X/Twitter API v2 client for publishing tweets using OAuth1.0a."""
    
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
        self.base_url = "https://api.twitter.com/2"
    
    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate OAuth1.0a signature for X API requests."""
        # Encode parameters
        encoded_params = {
            urllib.parse.quote(str(k), safe=''): urllib.parse.quote(str(v), safe='')
            for k, v in params.items()
        }
        
        # Create parameter string
        param_string = '&'.join(f"{k}={v}" for k, v in sorted(encoded_params.items()))
        
        # Create signature base string
        encoded_url = urllib.parse.quote(url, safe='')
        signature_base_string = f"{method.upper()}&{encoded_url}&{urllib.parse.quote(param_string, safe='')}"
        
        # Create signing key
        signing_key = f"{urllib.parse.quote(self.api_secret, safe='')}&{urllib.parse.quote(self.access_token_secret, safe='')}"
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return urllib.parse.quote(signature, safe='')
    
    def _generate_oauth_headers(self, method: str, url: str, params: Dict[str, str]) -> Dict[str, str]:
        """Generate OAuth1.0a headers for X API requests."""
        timestamp = str(int(time.time()))
        nonce = hashlib.sha256(timestamp.encode()).hexdigest()
        
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_token': self.access_token,
            'oauth_signature_method': 'HMAC-SHA256',
            'oauth_timestamp': timestamp,
            'oauth_nonce': nonce,
            'oauth_version': '1.0'
        }
        
        # Combine all params for signature
        all_params = {**oauth_params, **params}
        signature = self._generate_oauth_signature(method, url, all_params)
        oauth_params['oauth_signature'] = signature
        
        # Create OAuth header
        oauth_header = 'OAuth ' + ', '.join(
            f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
            for k, v in sorted(oauth_params.items())
        )
        
        return {'Authorization': oauth_header}
    
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
            Dict with keys: success, post_id, post_url
        """
        # Idempotency check - skip if already has post_id
        existing_post_id = kwargs.get("post_id")
        if existing_post_id:
            logger.info(f"Tweet already published with post_id: {existing_post_id}")
            return {
                "success": True,
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
            logger.error("X API credentials not fully configured")
            return {
                "success": False,
                "post_id": None,
                "post_url": None,
                "error": "X API credentials not fully configured"
            }
        
        # Real X API v2 implementation
        url = f"{self.base_url}/tweets"
        
        # Prepare request body
        body = {"text": text}
        
        # Generate OAuth headers
        headers = self._generate_oauth_headers("POST", url, body)
        headers["Content-Type"] = "application/json"
        
        try:
            response = await self.http.post(url, json=body, headers=headers)
            
            # Handle rate limiting
            if response.status_code == 429:
                rate_limit_reset = response.headers.get("x-rate-limit-reset")
                logger.warning(f"X API rate limit hit. Reset at: {rate_limit_reset}")
                raise httpx.HTTPStatusError(
                    "Rate limit exceeded",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract tweet ID and construct URL
            tweet_id = data.get("data", {}).get("id")
            if not tweet_id:
                raise ValueError("X API response missing tweet ID")
            
            post_url = f"https://x.com/i/status/{tweet_id}"
            
            logger.info(f"Successfully published to X: {post_url}")
            
            return {
                "success": True,
                "post_id": tweet_id,
                "post_url": post_url
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"X API request failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"X client error: {e}")
            raise
    
    @retry(retry=retry_if_exception(is_transient_error), stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def search(self, query: str, max_results: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Search for recent tweets using X API v2 recent search endpoint.
        
        Args:
            query: Search query (supports X search operators)
            max_results: Maximum number of results to return (1-100)
            **kwargs: Additional parameters (e.g., tweet_fields, expansions)
        
        Returns:
            Dict with keys: success, data (list of tweets), meta (pagination info)
        """
        # Validate query first before checking enabled status
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        # Validate max_results
        if not 1 <= max_results <= 100:
            raise ValueError("max_results must be between 1 and 100")
        
        # Check if search is enabled
        if not getattr(settings, "X_SEARCH_ENABLED", False):
            logger.info("X/Twitter search disabled (X_SEARCH_ENABLED=false)")
            return {
                "success": True,
                "data": [],
                "meta": {"result_count": 0}
            }
        
        # Check if credentials are configured
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.warning("X API credentials not fully configured, returning empty results")
            return {
                "success": True,
                "data": [],
                "meta": {"result_count": 0}
            }
        
        # Real X API v2 search implementation
        url = f"{self.base_url}/tweets/search/recent"
        
        # Prepare query parameters
        params = {
            "query": query,
            "max_results": str(max_results),
            "tweet.fields": "created_at,author_id,public_metrics,lang,reply_settings,source",
            "expansions": "author_id"
        }
        
        # Generate OAuth headers
        headers = self._generate_oauth_headers("GET", url, params)
        
        try:
            response = await self.http.get(url, params=params, headers=headers)
            
            # Handle rate limiting
            if response.status_code == 429:
                rate_limit_reset = response.headers.get("x-rate-limit-reset")
                logger.warning(f"X API rate limit hit. Reset at: {rate_limit_reset}")
                raise httpx.HTTPStatusError(
                    "Rate limit exceeded",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            
            data = response.json()
            
            tweets = data.get("data", [])
            meta = data.get("meta", {})
            
            logger.info(f"X search returned {len(tweets)} results for query: {query}")
            
            return {
                "success": True,
                "data": tweets,
                "meta": meta
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"X API search failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"X search error: {e}")
            raise
    
    async def close(self):
        await self.http.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
