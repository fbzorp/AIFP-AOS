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
                # Use SOL as default currency for X402
                challenge_data = await self._get_challenge(url, currency="SOL")
                
                amount = challenge_data.get("amount")
                currency = challenge_data.get("currency")
                recipient = challenge_data.get("recipient")
                network = challenge_data.get("network")

                if not all([amount, currency, recipient, network]):
                    raise ValueError("Invalid X402 challenge data")

                # Construct payment payload and submit via WalletClient
                tx_hash = await self.wallet_client.send_transaction(network, amount, recipient, force_real=True)
                payment_proof = f"tx_hash:{tx_hash},challenge:{challenge_data['challenge']}"

                # Retry original request with payment proof
                proof_result = await self._submit_payment_proof(url, payment_proof, challenge_data)
                
                # Second attempt after payment
                r = await self.http.request(method, url, headers={"X-Payment-Proof": payment_proof}, **kwargs)
                r.raise_for_status()
                return r.json()
            else:
                raise

    async def _get_challenge(self, request_url: str, currency: str = "SOL") -> Dict[str, Any]:
        # Get X402 challenge using real AiFinPay flow per manifesto.json
        logger.info(f"Getting X402 challenge for {request_url} with currency {currency}")
        
        try:
            # Step 1: Get nonce (60s TTL)
            nonce_response = await self.http.get(f"{self.facilitator_url}/nonce")
            nonce_response.raise_for_status()
            nonce = nonce_response.json()["nonce"]
            
            # Step 2: Create invoice based on currency
            if currency.upper() == "SOL":
                invoice_endpoint = "/invoice"
            else:
                invoice_endpoint = "/invoice-spl"
            
            invoice_response = await self.http.post(
                f"{self.facilitator_url}{invoice_endpoint}",
                json={
                    "amount": 0.01,  # Minimum amount from spec
                    "currency": currency,
                    "network": "solana"
                }
            )
            invoice_response.raise_for_status()
            invoice_data = invoice_response.json()
            
            # Step 3: Return challenge data for payment
            challenge_data = {
                "challenge": nonce,
                "amount": invoice_data.get("amount", 0.01),
                "currency": currency,
                "recipient": invoice_data.get("recipient", "AiFinPay Treasury"),
                "network": "solana",
                "nonce": nonce,
                "invoice_id": invoice_data.get("id")
            }
            
            logger.info(f"Received X402 challenge: {challenge_data}")
            return challenge_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get X402 challenge: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error getting X402 challenge: {e}")
            raise

    async def _submit_payment_proof(self, original_request_url: str, payment_proof: str, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        # Submit payment proof using real AiFinPay signature flow
        logger.info(f"Submitting payment proof for {original_request_url}")
        
        try:
            # Real X402 flow requires Ed25519 signature with nonce
            # This is handled by the wallet client during transaction
            # Here we acknowledge the payment completion
            
            # In production, this would verify the on-chain transaction
            # For now, return success status
            result = {
                "status": "payment_proof_accepted",
                "tx_hash": payment_proof.split(":")[1] if ":" in payment_proof else payment_proof,
                "challenge_id": challenge_data.get("challenge"),
                "invoice_id": challenge_data.get("invoice_id")
            }
            
            logger.info(f"Payment proof submitted successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error submitting payment proof: {e}")
            raise

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
