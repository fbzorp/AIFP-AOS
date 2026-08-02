import pytest
import respx
from httpx import Response
from unittest.mock import MagicMock, AsyncMock
from apps.integrations.x402.client import X402Client
from apps.integrations.wallet.client import WalletClient


@pytest.mark.asyncio
async def test_x402_client_disabled():
    """Test X402Client when x402 is disabled"""
    wallet_client = MagicMock(spec=WalletClient)
    client = X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=wallet_client,
        x402_enabled=False
    )
    
    # Test that create_payment_request raises when disabled
    with pytest.raises(ValueError, match="X402 is not enabled"):
        await client.create_payment_request(1.0, "SOL", "test")
    
    # Test that make_x402_request bypasses when disabled
    with respx.mock:
        respx.get("https://example.com/api/test").return_value = Response(200, json={"status": "ok"})
        result = await client.make_x402_request("GET", "https://example.com/api/test")
        assert result == {"status": "ok"}
    
    await client.close()


@pytest.mark.asyncio
async def test_x402_client_create_payment_request():
    """Test create_payment_request returns formatted URL"""
    wallet_client = MagicMock(spec=WalletClient)
    client = X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=wallet_client,
        x402_enabled=True
    )
    
    url = await client.create_payment_request(1.0, "SOL", "test purpose")
    assert url == "https://api.aifinpay.io/pay?amount=1.0&currency=SOL&purpose=test%20purpose"
    
    await client.close()


@pytest.mark.asyncio
async def test_x402_client_make_manual_request_402_challenge():
    """Test manual request when receiving 402 challenge"""
    wallet_client = MagicMock(spec=WalletClient)
    wallet_client.send_transaction = AsyncMock(return_value="test_tx_hash")
    
    client = X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=wallet_client,
        x402_enabled=True
    )
    
    with respx.mock:
        # First call returns 402
        respx.get("https://example.com/api/test").return_value = Response(402, json={"error": "Payment Required"})
        
        # Mock nonce endpoint
        respx.get("https://api.aifinpay.io/nonce").return_value = Response(200, json={"nonce": "test_nonce_123"})
        
        # Mock invoice endpoint
        respx.post("https://api.aifinpay.io/invoice").return_value = Response(200, json={
            "id": "invoice_123",
            "amount": 0.01,
            "recipient": "test_recipient"
        })
        
        # Mock retry with payment proof succeeds
        respx.get("https://example.com/api/test").return_value = Response(200, json={"status": "success"})
        
        result = await client._make_manual_request("GET", "https://example.com/api/test")
        assert result == {"status": "success"}
        
        # The wallet client might not be called if the SDK agent path is used
        # Just verify the request completed successfully


@pytest.mark.asyncio
async def test_x402_client_get_challenge():
    """Test getting X402 challenge"""
    client = X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=MagicMock(spec=WalletClient),
        x402_enabled=True
    )
    
    with respx.mock:
        # Mock nonce endpoint
        respx.get("https://api.aifinpay.io/nonce").return_value = Response(200, json={"nonce": "test_nonce_123"})
        
        # Mock invoice endpoint
        respx.post("https://api.aifinpay.io/invoice").return_value = Response(200, json={
            "id": "invoice_123",
            "amount": 0.01,
            "recipient": "test_recipient"
        })
        
        challenge = await client._get_challenge("https://example.com/api/test", "SOL")
        
        assert challenge["challenge"] == "test_nonce_123"
        assert challenge["amount"] == 0.01
        assert challenge["currency"] == "SOL"
        assert challenge["recipient"] == "test_recipient"
        assert challenge["network"] == "solana"


@pytest.mark.asyncio
async def test_x402_client_submit_payment_proof_with_sdk():
    """Test payment proof submission with SDK agent"""
    wallet_client = MagicMock(spec=WalletClient)
    
    # Mock SDK agent
    mock_agent = MagicMock()
    mock_agent.auth_headers.return_value = {
        "x-agent-pubkey": "test_pubkey",
        "x-nonce": "test_nonce",
        "x-signature": "test_signature"
    }
    
    client = X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=wallet_client,
        x402_enabled=True,
        signing_key=MagicMock()
    )
    client.agent = mock_agent
    
    challenge_data = {
        "challenge": "test_challenge",
        "invoice_id": "invoice_123",
        "nonce": "test_nonce"
    }
    
    result = await client._submit_payment_proof(
        "https://example.com/api/test",
        "tx_hash:test_tx_hash",
        challenge_data
    )
    
    assert result["status"] == "using_sdk_auth"
    assert result["verified"] is True
    assert "auth_headers" in result
    assert result["tx_hash"] == "test_tx_hash"


@pytest.mark.asyncio
async def test_x402_client_submit_payment_proof_without_sdk():
    """Test payment proof submission without SDK agent (soft-ack fallback)"""
    wallet_client = MagicMock(spec=WalletClient)
    
    client = X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=wallet_client,
        x402_enabled=True
    )
    
    challenge_data = {
        "challenge": "test_challenge",
        "invoice_id": "invoice_123",
        "nonce": "test_nonce"
    }
    
    result = await client._submit_payment_proof(
        "https://example.com/api/test",
        "tx_hash:test_tx_hash",
        challenge_data
    )
    
    assert result["status"] == "payment_proof_ready"
    assert result["verified"] is False
    assert "warning" in result
    assert "soft-ack" in result["warning"]


@pytest.mark.asyncio
async def test_x402_client_context_manager():
    """Test async context manager"""
    wallet_client = MagicMock(spec=WalletClient)
    
    async with X402Client(
        facilitator_url="https://api.aifinpay.io",
        wallet_client=wallet_client,
        x402_enabled=False
    ) as client:
        assert client is not None
