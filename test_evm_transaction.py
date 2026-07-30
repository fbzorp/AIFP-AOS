import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.integrations.wallet.client import WalletClient
from apps.api.config import settings

async def test_evm_transaction():
    print("=== TESTING REAL EVM BASE SEPOLIA TRANSACTION ===")
    
    wallet = WalletClient(
        solana_rpc_url=settings.SOLANA_RPC_URL,
        evm_rpc_url=settings.EVM_RPC_URL,
        solana_private_key=settings.SOLANA_PRIVATE_KEY,
        evm_private_key=settings.EVM_PRIVATE_KEY,
        per_transaction_limit=50.0,
        dry_run=False  # Enable real transactions
    )
    
    try:
        # Use a recipient from the allowlist
        recipient = "0x71ce0fb1a99dcc187fe86cefb9fba7c12082ac03"
        amount_eth = 0.0001  # Small amount for testing
        
        print(f"Sending {amount_eth} ETH to {recipient}")
        print(f"RPC URL: {settings.EVM_RPC_URL}")
        
        tx_hash = await wallet.send_transaction(
            network='evm',
            amount=amount_eth,
            recipient_address=recipient,
            force_real=True
        )
        
        print(f"Transaction sent: {tx_hash}")
        print(f"Explorer URL: https://sepolia.basescan.org/tx/{tx_hash}")
        
        return {
            "status": "success",
            "tx_hash": tx_hash,
            "explorer_url": f"https://sepolia.basescan.org/tx/{tx_hash}",
            "amount": amount_eth,
            "recipient": recipient
        }
        
    except Exception as e:
        print(f"EVM transaction failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    result = asyncio.run(test_evm_transaction())
    
    with open("evm_transaction_evidence.txt", "w") as f:
        f.write("=== REAL EVM BASE SEPOLIA TRANSACTION EVIDENCE ===\n")
        f.write(f"Status: {result['status']}\n")
        if result.get("status") == "success":
            f.write(f"TX Hash: {result['tx_hash']}\n")
            f.write(f"Explorer URL: {result['explorer_url']}\n")
            f.write(f"Amount: {result['amount']} ETH\n")
            f.write(f"Recipient: {result['recipient']}\n")
        else:
            f.write(f"Error: {result.get('error', 'Unknown error')}\n")
    
    print("\nEVM transaction evidence written to evm_transaction_evidence.txt")