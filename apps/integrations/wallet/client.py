import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Placeholder for actual Solana/EVM client libraries
class MockSolanaClient:
    async def send_transaction(self, signed_tx: str) -> str:
        return "mock_solana_tx_hash_123"

class MockEVMClient:
    async def send_transaction(self, signed_tx: str) -> str:
        return "mock_evm_tx_hash_456"

class WalletClient:
    def __init__(
        self,
        solana_rpc_url: str,
        evm_rpc_url: Optional[str],
        solana_private_key: Optional[str],
        evm_private_key: Optional[str],
        per_transaction_limit: float,
        dry_run: bool = True
    ):
        self.solana_rpc_url = solana_rpc_url
        self.evm_rpc_url = evm_rpc_url
        self.solana_private_key = solana_private_key
        self.evm_private_key = evm_private_key
        self.per_transaction_limit = per_transaction_limit
        self.dry_run = dry_run
        
        # Initialize mock clients for now
        self.solana_client = MockSolanaClient()
        self.evm_client = MockEVMClient()
        
        logger.info(f"WalletClient initialized (dry_run={dry_run}, limit={per_transaction_limit})")

    async def send_transaction(
        self, 
        network: str, 
        amount: float, 
        recipient_address: str,
        transaction_data: Optional[Dict[str, Any]] = None
    ) -> str:
        if amount > self.per_transaction_limit:
            raise ValueError(f"Transaction amount {amount} exceeds per-transaction limit of {self.per_transaction_limit}")

        if self.dry_run or (network == "solana" and not self.solana_private_key) or (network == "evm" and not self.evm_private_key):
            logger.info(f"[DRY RUN] Sending {amount} on {network} to {recipient_address}")
            return f"fake_tx_hash_dry_run_{network}_{amount}"

        if network == "solana":
            return await self.solana_client.send_transaction("mock_signed_solana_tx")
        elif network == "evm":
            return await self.evm_client.send_transaction("mock_signed_evm_tx")
        else:
            raise ValueError(f"Unsupported network: {network}")

    async def transfer(self, network: str, to_address: str, amount: float, currency: str) -> dict:
        # For backward compatibility or simpler usage
        tx_hash = await self.send_transaction(network, amount, to_address)
        
        # Build explorer URL
        tx_url = "https://explorer.example.com"
        if network == "solana":
            tx_url = f"https://explorer.solana.com/tx/{tx_hash}?cluster=devnet"
        elif network == "evm":
            tx_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"
            
        return {
            "status": "success",
            "tx_hash": tx_hash,
            "tx_url": tx_url
        }
