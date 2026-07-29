import httpx
import logging
from typing import Optional, Dict, Any
from apps.integrations.wallet.client import WalletClient

logger = logging.getLogger(__name__)

class X402Client:
    def __init__(
        self, 
        facilitator_url: Optional[str],
        wallet_client: WalletClient,
        x402_enabled: bool = False
    ):
        self.facilitator_url = facilitator_url
        self.wallet_client = wallet_client
        self.x402_enabled = x402_enabled
        self.http = httpx.AsyncClient()
        logger.info(f"X402Client initialized (enabled={x402_enabled}, facilitator={facilitator_url})")

    async def create_payment_request(self, amount: float, currency: str, purpose: str) -> str:
        if not self.x402_enabled:
            raise ValueError("X402 is not enabled")
            
        # Real implementation would call the facilitator API
        logger.info(f"Creating X402 payment request for {amount} {currency} - {purpose}")
        return f"{self.facilitator_url}/pay?amount={amount}&currency={currency}&purpose={purpose.replace(' ', '%20')}"

    async def make_x402_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        if not self.x402_enabled:
            logger.info(f"X402 is disabled. Proceeding with original request to {url}")
            r = await self.http.request(method, url, **kwargs)
            r.raise_for_status()
            return r.json()

        # First attempt: make the original request, expecting a 402 challenge
        try:
            r = await self.http.request(method, url, **kwargs)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                logger.info(f"Received 402 challenge for {url}")
                challenge_data = await self._get_challenge(url)
                
                amount = challenge_data.get("amount")
                currency = challenge_data.get("currency")
                recipient = challenge_data.get("recipient")
                network = challenge_data.get("network")

                if not all([amount, currency, recipient, network]):
                    raise ValueError("Invalid X402 challenge data")

                # Construct payment payload and submit via WalletClient
                tx_hash = await self.wallet_client.send_transaction(network, amount, recipient)
                payment_proof = f"tx_hash:{tx_hash},challenge:{challenge_data['challenge']}"

                # Retry original request with payment proof
                await self._submit_payment_proof(url, payment_proof)
                
                # Second attempt after payment
                r = await self.http.request(method, url, headers={"X-Payment-Proof": payment_proof}, **kwargs)
                r.raise_for_status()
                return r.json()
            else:
                raise

    async def _get_challenge(self, request_url: str) -> Dict[str, Any]:
        # Get a 402 challenge from the facilitator or directly from the target service
        logger.info(f"Getting X402 challenge for {request_url}")
        # This will be replaced with real implementation
        return {
            "challenge": "x402_challenge_token_123",
            "amount": 0.01,
            "currency": "SOL",
            "recipient": "some_solana_address",
            "network": "solana"
        }

    async def _submit_payment_proof(self, original_request_url: str, payment_proof: str) -> Dict[str, Any]:
        # Submit payment proof to the facilitator or target service
        logger.info(f"Submitting payment proof for {original_request_url} with {payment_proof}")
        # This will be replaced with real implementation
        return {"status": "payment_proof_accepted"}

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
