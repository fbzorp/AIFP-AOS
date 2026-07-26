
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, Dict, Any

class AiFinPayClient:
    def __init__(
        self, 
        base_url: str, 
        api_key: Optional[str], 
        timeout: float = 20,
        dry_run: bool = False
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.dry_run = dry_run
        self.http = httpx.AsyncClient(timeout=timeout)

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        if self.dry_run or not self.api_key:
            # Deterministic fake response for dry-run
            print(f"Dry run: {method} {self.base_url}{path} with {kwargs}")
            return {"status": "dry_run_success", "id": "fake_tx_id_123", "amount": kwargs.get("json", {}).get("amount"), "currency": kwargs.get("json", {}).get("currency"), "tx_hash": "fake_tx_hash_dry_run"}

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Idempotency-Key"] = kwargs.pop("idempotency_key", str(hash(f"{method}-{path}-{kwargs}")))

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
        async def _send_request():
            r = await self.http.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
            r.raise_for_status()
            return r.json()
        
        return await _send_request()

    async def create_payment(self, amount: float, currency: str, purpose: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return await self._request(
            "POST", 
            "/api/v1/payments", 
            json={
                "amount": amount, 
                "currency": currency, 
                "purpose": purpose
            },
            idempotency_key=idempotency_key
        )

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/payments/{payment_id}")

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
