import httpx
import logging
from typing import Optional, Dict, Any
from apps.integrations.wallet.client import WalletClient
from aifinpay import Agent
from nacl.signing import SigningKey
import base58

logger = logging.getLogger(__name__)

class X402Client:
    def __init__(
        self, 
        facilitator_url: Optional[str],
        wallet_client: WalletClient,
        x402_enabled: bool = False,
        signing_key: Optional[SigningKey] = None,
        signing_key_base58: Optional[str] = None
    ):
        self.facilitator_url = facilitator_url
        self.wallet_client = wallet_client
        self.x402_enabled = x402_enabled
        self.http = httpx.AsyncClient()
        
        # Initialize official AiFinPay SDK agent if signing key is provided
        self.agent = None
        if x402_enabled:
            # Convert base58 secret key to SigningKey if provided
            if signing_key_base58 and not signing_key:
                try:
                    # Base58 decode to get raw bytes, then create SigningKey
                    key_bytes = base58.b58decode(signing_key_base58)
                    # Ed25519 keys are 64 bytes (32 bytes seed + 32 bytes public)
                    if len(key_bytes) >= 32:
                        signing_key = SigningKey(key_bytes[:32])
                        logger.info("Successfully converted base58 secret key to SigningKey")
                except Exception as e:
                    logger.warning(f"Failed to convert base58 secret key: {e}")
            
            if signing_key:
                self.agent = Agent(
                    signing_key=signing_key,
                    base_url=facilitator_url or "https://api.aifinpay.io",
                    timeout=30
                )
                logger.info(f"X402Client initialized with official SDK agent (enabled={x402_enabled}, facilitator={facilitator_url})")
            else:
                logger.info(f"X402Client initialized without SDK agent (no signing key provided) (enabled={x402_enabled}, facilitator={facilitator_url})")
        else:
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

        # Use official SDK agent if available
        if self.agent:
            return await self._make_sdk_request(method, url, **kwargs)
        
        # Fallback to manual implementation
        return await self._make_manual_request(method, url, **kwargs)

    async def _make_sdk_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Use official AiFinPay SDK for x402 request handling"""
        try:
            logger.info(f"Using official SDK for x402 request to {url}")
            
            # Convert async httpx kwargs to synchronous requests kwargs
            sync_kwargs = {}
            if 'headers' in kwargs:
                sync_kwargs['headers'] = kwargs['headers']
            if 'json' in kwargs:
                sync_kwargs['json'] = kwargs['json']
            if 'params' in kwargs:
                sync_kwargs['params'] = kwargs['params']
            if 'timeout' in kwargs:
                sync_kwargs['timeout'] = kwargs['timeout']
            
            # Use SDK's pay method which handles 402 automatically
            response = self.agent.pay(
                url=url,
                method=method,
                max_retries=1,
                **sync_kwargs
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"SDK request failed: {e}")
            # Fallback to manual implementation on SDK failure
            logger.info("Falling back to manual x402 implementation")
            return await self._make_manual_request(method, url, **kwargs)

    async def _make_manual_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Manual x402 implementation using httpx"""
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

                # Prepare auth headers for retry
                proof_result = await self._submit_payment_proof(url, payment_proof, challenge_data)
                
                # Second attempt after payment with proper X402 auth headers
                retry_headers = kwargs.get('headers', {}).copy()
                
                if proof_result.get("status") == "using_sdk_auth":
                    # Use SDK auth headers for the retry
                    retry_headers.update(proof_result["auth_headers"])
                    logger.info(f"Retrying with SDK auth headers")
                else:
                    # Fallback to manual proof construction
                    retry_headers["X-Payment-Proof"] = payment_proof
                    logger.info(f"Retrying with manual payment proof header")
                
                r = await self.http.request(method, url, headers=retry_headers, **kwargs)
                r.raise_for_status()
                return r.json()
            else:
                raise

    async def _get_challenge(self, request_url: str, currency: str = "SOL") -> Dict[str, Any]:
        # Get X402 challenge using real AiFinPay flow per manifesto.json
        logger.info(f"Getting X402 challenge for {request_url} with currency {currency}")
        
        try:
            # Step 1: Get nonce (60s TTL) - working endpoint
            nonce_response = await self.http.get(f"{self.facilitator_url}/nonce")
            nonce_response.raise_for_status()
            nonce = nonce_response.json()["nonce"]
            
            # Step 2: Create invoice based on currency (using correct manifesto.json paths)
            # manifesto.json actions: "reserve_seat_sol":"POST /api/invoice", "reserve_seat_spl":"POST /api/invoice-spl"
            if currency.upper() == "SOL":
                invoice_endpoint = "/api/invoice"  # reserve_seat_sol
            else:
                invoice_endpoint = "/api/invoice-spl"  # reserve_seat_spl
            
            # Build proper invoice request per manifesto.json
            invoice_payload = {
                "amount": 0.01,  # Minimum amount from spec
                "currency": currency,
                "network": "solana"
            }
            
            # Add auth headers if SDK agent is available
            headers = {}
            if self.agent:
                auth_headers = self.agent.auth_headers()
                headers.update(auth_headers)
                logger.info(f"Using SDK auth headers for invoice request")
            
            invoice_response = await self.http.post(
                f"{self.facilitator_url}{invoice_endpoint}",
                json=invoice_payload,
                headers=headers
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
            logger.error(f"Failed to get X402 challenge: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting X402 challenge: {e}")
            raise

    async def _submit_payment_proof(self, original_request_url: str, payment_proof: str, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        # Submit payment proof using real AiFinPay signature flow
        logger.info(f"Submitting payment proof for {original_request_url}")
        
        try:
            # Per manifesto.json, there is no separate verify-proof endpoint
            # The proper X402 flow uses SDK auth headers (x-agent-pubkey, x-nonce, x-signature)
            # directly in the original request retry after payment
            
            # If SDK agent is available, use its auth headers for the retry
            if self.agent:
                auth_headers = self.agent.auth_headers()
                logger.info(f"Using SDK auth headers for payment proof retry")
                return {
                    "status": "using_sdk_auth",
                    "auth_headers": auth_headers,
                    "tx_hash": payment_proof.split(":")[1] if ":" in payment_proof else payment_proof,
                    "challenge_id": challenge_data.get("challenge"),
                    "invoice_id": challenge_data.get("invoice_id")
                }
            else:
                # Fallback: return the payment proof for manual header construction
                logger.warning("No SDK agent available, returning payment proof for manual retry")
                return {
                    "status": "payment_proof_ready",
                    "tx_hash": payment_proof.split(":")[1] if ":" in payment_proof else payment_proof,
                    "challenge_id": challenge_data.get("challenge"),
                    "invoice_id": challenge_data.get("invoice_id"),
                    "nonce": challenge_data.get("nonce")
                }
            
        except Exception as e:
            logger.error(f"Error preparing payment proof: {e}")
            raise

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
