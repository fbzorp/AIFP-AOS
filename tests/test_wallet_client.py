import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from apps.integrations.wallet.client import WalletClient


@pytest.mark.asyncio
async def test_wallet_client_dry_run_mode():
    """Test dry run mode behavior"""
    client = WalletClient(
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        evm_rpc_url=None,
        solana_private_key=None,
        evm_private_key=None,
        per_transaction_limit=1000.0,
        dry_run=True
    )
    
    # In dry run mode, should return mock result
    result = await client.send_transaction("solana", 0.01, "test_recipient", force_real=False)
    assert "dry_run" in result
    assert "solana" in result


@pytest.mark.asyncio
async def test_wallet_client_per_transaction_limit():
    """Test per-transaction limit enforcement"""
    client = WalletClient(
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        evm_rpc_url=None,
        solana_private_key=None,
        evm_private_key=None,
        per_transaction_limit=100.0,
        dry_run=True
    )
    
    # Should reject amount exceeding limit
    with pytest.raises(ValueError, match="exceeds per-transaction limit"):
        await client.send_transaction("solana", 150.0, "test_recipient")


@pytest.mark.asyncio
async def test_wallet_client_dry_run_accepts_transaction():
    """Test that dry run mode accepts transactions within limit"""
    client = WalletClient(
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        evm_rpc_url=None,
        solana_private_key=None,
        evm_private_key=None,
        per_transaction_limit=100.0,
        dry_run=True
    )
    
    # Should accept amount within limit
    result = await client.send_transaction("solana", 50.0, "test_recipient")
    assert "dry_run" in result


@pytest.mark.asyncio
async def test_wallet_client_force_real_with_invalid_key():
    """Test force_real parameter with invalid key"""
    client = WalletClient(
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        evm_rpc_url=None,
        solana_private_key="invalid_key",
        evm_private_key=None,
        per_transaction_limit=1000.0,
        dry_run=True
    )
    
    # Even with dry_run=True, force_real=True should attempt real transaction
    # But with invalid key, it will fail
    with pytest.raises(Exception):
        await client.send_transaction("solana", 0.01, "test_recipient", force_real=True)


@pytest.mark.asyncio
async def test_wallet_client_network_detection():
    """Test network detection based on currency"""
    client = WalletClient(
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        evm_rpc_url="https://mainnet.infura.io/v3/test",
        solana_private_key=None,
        evm_private_key=None,
        per_transaction_limit=1000.0,
        dry_run=True
    )
    
    # Test that different currencies work in dry run mode
    result = await client.send_transaction("solana", 0.01, "test_recipient")
    assert "dry_run" in result
    
    result = await client.send_transaction("usdc", 0.01, "test_recipient")
    assert "dry_run" in result
    
    result = await client.send_transaction("eth", 0.01, "test_recipient")
    assert "dry_run" in result


@pytest.mark.asyncio
async def test_wallet_client_initialization():
    """Test wallet client initialization"""
    client = WalletClient(
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        evm_rpc_url="https://mainnet.infura.io/v3/test",
        solana_private_key=None,
        evm_private_key=None,
        per_transaction_limit=1000.0,
        dry_run=True
    )
    
    assert client.solana_rpc_url == "https://api.mainnet-beta.solana.com"
    assert client.evm_rpc_url == "https://mainnet.infura.io/v3/test"
    assert client.per_transaction_limit == 1000.0
    assert client.dry_run is True
