
import httpx
from typing import Optional, Dict, Any
from apps.integrations.wallet.client import WalletClient

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

    async def _get_challenge(self, request_url: str) -> Dict[str, Any]:
        # Simulate getting a 402 challenge from the facilitator or directly from the target service
        print(f"Simulating X402 challenge for {request_url}")
        return {
            "challenge": "x402_challenge_token_123",
            "amount": 0.01,
            "currency": "SOL",
            "recipient": "some_solana_address",
            "network": "solana"
        }

    async def _submit_payment_proof(self, original_request_url: str, payment_proof: str) -> Dict[str, Any]:
        # Simulate submitting payment proof to the facilitator or target service
        print(f"Simulating submitting payment proof for {original_request_url} with {payment_proof}")
        return {"status": "payment_proof_accepted"}

    async def make_x402_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        if not self.x402_enabled:
            print(f"X402 is disabled. Proceeding with original request to {url}")
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
                print(f"Received 402 challenge for {url}")
                challenge_data = await self._get_challenge(url) # In a real scenario, challenge data would be in e.response headers/body
                
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
                # In a real scenario, payment proof would be in a specific header (e.g., X-Payment-Proof)
                # For now, we'll just simulate success after payment
                await self._submit_payment_proof(url, payment_proof)
                
                # Second attempt after payment
                r = await self.http.request(method, url, headers={"X-Payment-Proof": payment_proof}, **kwargs) # Simulate sending proof
                r.raise_for_status()
                return r.json()
            else:
                raise # Re-raise other HTTP errors

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
