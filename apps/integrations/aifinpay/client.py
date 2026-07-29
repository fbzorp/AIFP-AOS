import httpx
import hashlib
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AiFinPayClient:
    def __init__(
        self, 
        base_url: str, 
        agent_secret: Optional[str] = None,
        agent_pubkey: Optional[str] = None,
        timeout: float = 20,
        dry_run: bool = False
    ):
        self.base_url = base_url.rstrip("/")
        self.agent_secret = agent_secret
        self.agent_pubkey = agent_pubkey
        self.dry_run = dry_run
        self.http = httpx.AsyncClient(timeout=timeout)
        logger.info(f"AiFinPayClient initialized (dry_run={dry_run})")

    async def _get_nonce(self) -> str:
        """Get a fresh nonce from the API (60s TTL)"""
        if self.dry_run:
            return "dry_run_nonce_123"
        
        response = await self.http.get(f"{self.base_url}/nonce")
        response.raise_for_status()
        data = response.json()
        return data["nonce"]

    def _sign_nonce(self, nonce: str) -> str:
        """Sign nonce with Ed25519 key"""
        if self.dry_run or not self.agent_secret:
            return "dry_run_signature"
        
        # In real implementation, use the aifinpay-agent SDK's signing
        # For now, return a placeholder
        # The signature should be: Ed25519(SHA256("AiFinPay-x402:{nonce}:{agent_pubkey}"), agent_keypair)
        try:
            from aifinpay import Agent
            agent = Agent.from_secret(self.agent_secret)
            message = f"AiFinPay-x402:{nonce}:{self.agent_pubkey}"
            signature = agent.sign(message)
            return signature
        except ImportError:
            logger.warning("aifinpay-agent not installed, using placeholder signature")
            return f"placeholder_signature_{nonce}"

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        if self.dry_run:
            logger.info(f"Dry run: {method} {self.base_url}{path}")
            return {"status": "dry_run_success", "id": "fake_tx_id_123"}

        headers = kwargs.pop("headers", {})
        
        # Add Ed25519 nonce-based auth headers
        nonce = await self._get_nonce()
        signature = self._sign_nonce(nonce)
        
        headers["x-agent-pubkey"] = self.agent_pubkey or ""
        headers["x-nonce"] = nonce
        headers["x-signature"] = signature

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
        async def _send_request():
            r = await self.http.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
            r.raise_for_status()
            return r.json()
        
        return await _send_request()

    async def create_invoice(self, amount: float, currency: str, network: str = "solana") -> Dict[str, Any]:
        """Create invoice - POST /api/invoice for SOL, POST /api/invoice-spl for USDC/USDT"""
        if currency.upper() == "SOL":
            endpoint = "/api/invoice"
        else:
            endpoint = "/api/invoice-spl"
        
        return await self._request(
            "POST",
            endpoint,
            json={
                "amount": amount,
                "currency": currency,
                "network": network
            }
        )

    async def get_seat(self, pubkey: str) -> Dict[str, Any]:
        """Get seat information - GET /api/seat/{pubkey}"""
        return await self._request("GET", f"/api/seat/{pubkey}")

    async def check_passport(self, pubkey: str) -> Dict[str, Any]:
        """Check passport status - GET /api/passport/{pubkey}"""
        return await self._request("GET", f"/api/passport/{pubkey}")

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
