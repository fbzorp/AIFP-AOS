import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

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
        
        # Initialize real clients
        self._solana_client = None
        self._evm_client = None
        
        # Always initialize clients if credentials are provided
        if solana_private_key:
            self._init_solana_client()
        if evm_private_key:
            self._init_evm_client()
        
        logger.info(f"WalletClient initialized (dry_run={dry_run}, limit={per_transaction_limit})")

    def _init_solana_client(self):
        """Initialize Solana client using solana-py"""
        if not self.solana_private_key:
            logger.warning("Solana private key not provided, skipping Solana client initialization")
            return
        
        try:
            from solana.rpc.async_api import AsyncClient
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            import base58
            
            self._solana_client = AsyncClient(self.solana_rpc_url)
            
            # Decode private key from base58
            keypair_bytes = base58.b58decode(self.solana_private_key)
            self._solana_keypair = Keypair.from_bytes(keypair_bytes)
            
            logger.info("Solana client initialized successfully")
        except ImportError:
            logger.warning("solana-py or solders not installed, Solana transactions will not work")
        except Exception as e:
            logger.error(f"Failed to initialize Solana client: {e}")

    def _init_evm_client(self):
        """Initialize EVM client using web3.py"""
        if not self.evm_private_key or not self.evm_rpc_url:
            logger.warning("EVM private key or RPC URL not provided, skipping EVM client initialization")
            return
        
        try:
            from web3 import Web3
            from eth_account import Account
            
            self._evm_client = Web3(Web3.HTTPProvider(self.evm_rpc_url))
            self._evm_account = Account.from_key(self.evm_private_key)
            
            logger.info("EVM client initialized successfully")
        except ImportError:
            logger.warning("web3.py or eth-account not installed, EVM transactions will not work")
        except Exception as e:
            logger.error(f"Failed to initialize EVM client: {e}")

    async def send_transaction(
        self, 
        network: str, 
        amount: float, 
        recipient_address: str,
        transaction_data: Optional[Dict[str, Any]] = None,
        force_real: bool = False
    ) -> str:
        if amount > self.per_transaction_limit:
            raise ValueError(f"Transaction amount {amount} exceeds per-transaction limit of {self.per_transaction_limit}")

        if not force_real and (self.dry_run or (network == "solana" and not self.solana_private_key) or (network == "evm" and not self.evm_private_key)):
            logger.info(f"[DRY RUN] Sending {amount} on {network} to {recipient_address}")
            return f"fake_tx_hash_dry_run_{network}_{amount}"

        if network == "solana":
            return await self._send_solana_transaction(amount, recipient_address)
        elif network == "evm":
            return await self._send_evm_transaction(amount, recipient_address)
        else:
            raise ValueError(f"Unsupported network: {network}")

    async def _send_solana_transaction(self, amount: float, recipient_address: str) -> str:
        """Send real Solana transaction"""
        if not self._solana_client:
            raise ValueError("Solana client not initialized")
        
        try:
            from solana.transaction import Transaction
            from solders.pubkey import Pubkey
            from solders.system_program import TransferParams, transfer
            from solders.signature import Signature
            import base58
            
            # Convert amount to lamports (1 SOL = 1,000,000,000 lamports)
            lamports = int(amount * 1_000_000_000)
            
            recipient_pubkey = Pubkey.from_string(recipient_address)
            
            # Create transfer instruction
            transfer_instruction = transfer(
                TransferParams(
                    from_pubkey=self._solana_keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )
            
            # Create transaction
            transaction = Transaction().add(transfer_instruction)
            
            # Get recent blockhash
            response = await self._solana_client.get_latest_blockhash()
            transaction.recent_blockhash = response.value.blockhash
            
            # Sign transaction properly
            transaction.sign(self._solana_keypair)
            
            # Serialize the signed transaction
            serialized_tx = bytes(transaction)
            
            # Send transaction
            result = await self._solana_client.send_raw_transaction(serialized_tx)
            tx_hash = str(result.value)
            
            logger.info(f"Solana transaction sent: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to send Solana transaction: {e}")
            raise

    async def _send_evm_transaction(self, amount: float, recipient_address: str) -> str:
        """Send real EVM transaction"""
        if not self._evm_client:
            raise ValueError("EVM client not initialized")
        
        try:
            # Convert amount to wei (1 ETH = 1,000,000,000,000,000,000 wei)
            amount_wei = self._evm_client.to_wei(amount, 'ether')
            
            # Build transaction
            transaction = {
                'to': recipient_address,
                'value': amount_wei,
                'gas': 21000,  # Standard gas limit for simple transfer
                'gasPrice': self._evm_client.eth.gas_price,
                'nonce': self._evm_client.eth.get_transaction_count(self._evm_account.address),
            }
            
            # Sign transaction
            signed_tx = self._evm_client.eth.account.sign_transaction(transaction, self.evm_private_key)
            
            # Send transaction (web3 v7 uses raw_transaction instead of rawTransaction)
            tx_hash = self._evm_client.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"EVM transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Failed to send EVM transaction: {e}")
            raise

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
