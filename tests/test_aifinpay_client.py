import pytest
import respx
from httpx import Response
from apps.integrations.aifinpay.client import AiFinPayClient


@pytest.mark.asyncio
async def test_aifinpay_client_dry_run():
    """Test AiFinPayClient in dry run mode"""
    client = AiFinPayClient(
        base_url="https://api.aifinpay.io",
        agent_secret="test_secret",
        agent_pubkey="test_pubkey",
        dry_run=True
    )
    
    # Test that dry run returns mock responses
    result = await client.create_invoice(1.0, "SOL")
    assert result == {"status": "dry_run_success", "id": "fake_tx_id_123"}
    
    result = await client.get_seat("test_pubkey")
    assert result == {"status": "dry_run_success", "id": "fake_tx_id_123"}
    
    result = await client.check_passport("test_pubkey")
    assert result == {"status": "dry_run_success", "id": "fake_tx_id_123"}
    
    await client.close()


@pytest.mark.asyncio
async def test_aifinpay_client_get_nonce_dry_run():
    """Test nonce generation in dry run mode"""
    client = AiFinPayClient(
        base_url="https://api.aifinpay.io",
        dry_run=True
    )
    
    nonce = await client._get_nonce()
    assert nonce == "dry_run_nonce_123"
    
    await client.close()


@pytest.mark.asyncio
async def test_aifinpay_client_sign_nonce_dry_run():
    """Test nonce signing in dry run mode"""
    client = AiFinPayClient(
        base_url="https://api.aifinpay.io",
        dry_run=True
    )
    
    signature = client._sign_nonce("test_nonce")
    assert signature == "dry_run_signature"
    
    await client.close()


@pytest.mark.asyncio
async def test_aifinpay_client_sign_nonce_missing_secret():
    """Test that signing raises error when secret is missing in non-dry-run mode"""
    client = AiFinPayClient(
        base_url="https://api.aifinpay.io",
        agent_secret=None,
        dry_run=False
    )
    
    with pytest.raises(ValueError, match="Agent secret is required"):
        await client._sign_nonce("test_nonce")
    
    await client.close()


@pytest.mark.asyncio
async def test_aifinpay_client_create_invoice_sol():
    """Test create_invoice for SOL currency"""
    client = AiFinPayClient(
        base_url="https://api.aifinpay.io",
        dry_run=True
    )
    
    result = await client.create_invoice(1.0, "SOL")
    assert result == {"status": "dry_run_success", "id": "fake_tx_id_123"}
    
    await client.close()


@pytest.mark.asyncio
async def test_aifinpay_client_create_invoice_usdc():
    """Test create_invoice for USDC currency"""
    client = AiFinPayClient(
        base_url="https://api.aifinpay.io",
        dry_run=True
    )
    
    result = await client.create_invoice(1.0, "USDC")
    assert result == {"status": "dry_run_success", "id": "fake_tx_id_123"}
    
    await client.close()


@pytest.mark.asyncio
async def test_aifinpay_client_context_manager():
    """Test async context manager"""
    async with AiFinPayClient(
        base_url="https://api.aifinpay.io",
        dry_run=True
    ) as client:
        result = await client.create_invoice(1.0, "SOL")
        assert result == {"status": "dry_run_success", "id": "fake_tx_id_123"}
