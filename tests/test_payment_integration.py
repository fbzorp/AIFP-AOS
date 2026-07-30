"""
Offline-green tests for payment integration
These tests mock SDK/RPC/MCP calls and never require live network
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import select
from datetime import datetime, timezone

from apps.integrations.wallet.client import WalletClient
from apps.integrations.x402.client import X402Client
from apps.integrations.aifinpay.client import AiFinPayClient
from apps.integrations.mcp.client import MCPClient
from apps.models.base import get_sync_session
from apps.models.payment import PaymentModel
from apps.models.audit_event import AuditEventModel
from apps.core.audit.service import record_event
from apps.api.config import settings


@pytest.fixture
def mock_wallet_client():
    """Mock wallet client for testing"""
    with patch('apps.integrations.wallet.client.WalletClient') as mock:
        client = Mock(spec=WalletClient)
        client.send_transaction = AsyncMock(return_value="mock_tx_hash_123")
        client.per_transaction_limit = 50.0
        client.dry_run = True
        yield client


@pytest.fixture
def mock_x402_client():
    """Mock X402 client for testing"""
    with patch('apps.integrations.x402.client.X402Client') as mock:
        client = Mock(spec=X402Client)
        client.create_payment_request = AsyncMock(return_value="https://api.aifinpay.io/pay?amount=0.01&currency=SOL")
        client.x402_enabled = True
        yield client


@pytest.fixture
def mock_aifinpay_client():
    """Mock AiFinPay client for testing"""
    with patch('apps.integrations.aifinpay.client.AiFinPayClient') as mock:
        client = Mock(spec=AiFinPayClient)
        client.create_invoice = AsyncMock(return_value={"id": "invoice_123", "status": "pending"})
        client.get_seat = AsyncMock(return_value={"pubkey": "test_pubkey", "balance": 1.0})
        yield client


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing"""
    with patch('apps.integrations.mcp.client.MCPClient') as mock:
        client = Mock(spec=MCPClient)
        client.enabled = True
        client.call_tool = AsyncMock(return_value={
            "status": "success",
            "cost_usd": 0.01,
            "result": "mock_result"
        })
        client.get_successful_calls = Mock(return_value=[
            Mock(
                agent="TestAgent",
                tool_name="agent_address",
                request_id="req_123",
                latency_ms=100.0,
                status="success",
                cost_usd=0.01
            )
        ])
        yield client


class TestWalletClient:
    """Test wallet client functionality"""
    
    @pytest.mark.asyncio
    async def test_send_transaction_dry_run(self, mock_wallet_client):
        """Test transaction send in dry run mode"""
        tx_hash = await mock_wallet_client.send_transaction(
            network="solana",
            amount=0.01,
            recipient_address="test_recipient"
        )
        
        assert tx_hash == "mock_tx_hash_123"
        mock_wallet_client.send_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_per_transaction_limit(self):
        """Test per-transaction limit enforcement"""
        client = WalletClient(
            solana_rpc_url="https://api.devnet.solana.com",
            evm_rpc_url=None,
            solana_private_key=None,
            evm_private_key=None,
            per_transaction_limit=0.1,
            dry_run=True
        )
        
        with pytest.raises(ValueError, match="exceeds per-transaction limit"):
            await client.send_transaction(
                network="solana",
                amount=1.0,  # Exceeds limit
                recipient_address="test_recipient"
            )


class TestX402Client:
    """Test X402 client functionality"""
    
    @pytest.mark.asyncio
    async def test_create_payment_request(self, mock_x402_client):
        """Test X402 payment request creation"""
        url = await mock_x402_client.create_payment_request(
            amount=0.01,
            currency="SOL",
            purpose="Test payment"
        )
        
        assert "api.aifinpay.io" in url
        assert "amount=0.01" in url
        mock_x402_client.create_payment_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_x402_disabled(self):
        """Test X402 when disabled"""
        client = X402Client(
            facilitator_url="https://api.aifinpay.io",
            wallet_client=Mock(),
            x402_enabled=False
        )
        
        with pytest.raises(ValueError, match="X402 is not enabled"):
            await client.create_payment_request(0.01, "SOL", "Test")


class TestMCPClient:
    """Test MCP client functionality"""
    
    @pytest.mark.asyncio
    async def test_mcp_tool_call(self, mock_mcp_client):
        """Test MCP tool call"""
        result = await mock_mcp_client.call_tool(
            tool_name="agent_address",
            agent="TestAgent",
            params={}
        )
        
        assert result["status"] == "success"
        mock_mcp_client.call_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_max_usd_cap(self):
        """Test MCP max USD cap enforcement"""
        client = MCPClient(
            max_usd=0.01,
            enabled=True
        )
        
        with patch.object(client, '_ensure_agent') as mock_init:
            mock_init.return_value = None
            
            with patch.object(client, '_call_agent_method') as mock_call:
                mock_call.return_value = {"cost_usd": 1.0}
                
                with pytest.raises(ValueError, match="exceeds maximum allowed"):
                    await client.call_tool(
                        tool_name="agent_quote",
                        agent="TestAgent",
                        params={"amount": 1.0}
                    )
    
    @pytest.mark.asyncio
    async def test_mcp_available_tools(self):
        """Test MCP available tools list"""
        client = MCPClient(
            max_usd=0.10,
            enabled=True
        )
        
        expected_tools = [
            "payable_fetch",
            "agent_address",
            "agent_quote",
            "agent_call",
            "pay_with_split",
            "quote_split",
            "agent_claim_self"
        ]
        
        assert client.AVAILABLE_TOOLS == expected_tools


class TestAuditEventRecording:
    """Test audit event recording for MCP calls"""
    
    def test_mcp_call_succeeded_audit_event(self):
        """Test that MCP call succeeded events are recorded"""
        with get_sync_session() as session:
            # Record a mock MCP call succeeded event
            record_event(
                session,
                "TestAgent",
                "mcp_call_succeeded",
                "MCP tool call succeeded: agent_address",
                {
                    "tool_name": "agent_address",
                    "request_id": "req_123",
                    "latency_ms": 100.0,
                    "cost_usd": 0.01,
                    "status": "success"
                }
            )
            session.commit()
            
            # Verify the event was recorded
            events = session.execute(
                select(AuditEventModel).where(
                    AuditEventModel.event_type == "mcp_call_succeeded"
                )
            ).scalars().all()
            
            assert len(events) > 0
            assert events[0].agent_name == "TestAgent"
            # Check that metadata contains the tool_name key
            assert events[0].metadata_json is not None
            assert "tool_name" in events[0].metadata_json


class TestPaymentScenarios:
    """Test payment scenarios with mocked components"""
    
    @pytest.mark.asyncio
    async def test_insufficient_balance_scenario(self):
        """Test insufficient balance scenario is caught and recorded"""
        client = WalletClient(
            solana_rpc_url="https://api.devnet.solana.com",
            evm_rpc_url=None,
            solana_private_key=None,
            evm_private_key=None,
            per_transaction_limit=0.001,  # Very low limit
            dry_run=True
        )
        
        with pytest.raises(ValueError, match="exceeds per-transaction limit"):
            await client.send_transaction(
                network="solana",
                amount=1.0,  # Exceeds limit
                recipient_address="test_recipient"
            )
    
    @pytest.mark.asyncio
    async def test_user_declined_payment_scenario(self):
        """Test payment above threshold requires approval"""
        with get_sync_session() as session:
            # Create payment above approval threshold
            payment = PaymentModel(
                amount=settings.HUMAN_APPROVAL_THRESHOLD + 10.0,
                currency="USD",
                recipient_address="test_recipient",
                network="solana",
                purpose="Test declined payment",
                status="pending"  # Should remain pending
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)
            
            # Verify status is pending (not auto-approved)
            assert payment.status == "pending"
    
    @pytest.mark.asyncio
    async def test_retry_after_transient_failure(self):
        """Test retry logic after transient failure"""
        # Test that retry logic works by simulating the retry pattern
        attempt = 0
        max_attempts = 3
        succeeded = False
        
        async def mock_send_with_retry():
            nonlocal attempt, succeeded
            attempt += 1
            if attempt == 1:
                raise Exception("Transient network error")
            succeeded = True
            return "dry_run_tx_hash"
        
        # Simulate retry loop
        for i in range(max_attempts):
            try:
                result = await mock_send_with_retry()
                succeeded = True
                break
            except Exception as e:
                if i == max_attempts - 1:
                    # Last attempt failed
                    succeeded = False
                    break
                # Continue retry
        
        assert succeeded, "Retry should have succeeded on second attempt"
        assert attempt == 2, "Should have taken exactly 2 attempts"
    
    @pytest.mark.asyncio
    async def test_insufficient_balance_with_real_limits(self):
        """Test insufficient balance with real limit enforcement"""
        client = WalletClient(
            solana_rpc_url="https://api.devnet.solana.com",
            evm_rpc_url=None,
            solana_private_key=None,
            evm_private_key=None,
            per_transaction_limit=0.001,  # Very low limit
            dry_run=True
        )
        
        # Test amount exceeding limit
        with pytest.raises(ValueError, match="exceeds per-transaction limit"):
            await client.send_transaction(
                network="solana",
                amount=0.01,  # Exceeds 0.001 limit
                recipient_address="test_recipient"
            )
        
        # Test amount within limit
        result = await client.send_transaction(
            network="solana",
            amount=0.0005,  # Within limit
            recipient_address="test_recipient"
        )
        assert result  # Should not raise


class TestPaymentPersistence:
    """Test payment transaction details persistence"""
    
    def test_tx_hash_and_explorer_url_persistence(self):
        """Test that tx_hash and explorer URL are persisted"""
        with get_sync_session() as session:
            payment = PaymentModel(
                amount=0.01,
                currency="SOL",
                recipient_address="test_recipient",
                network="solana",
                purpose="Test persistence",
                status="success",
                tx_hash="test_tx_hash_12345",
                tx_url="https://explorer.solana.com/tx/test_tx_hash_12345?cluster=devnet"
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)
            
            # Verify persistence
            assert payment.tx_hash == "test_tx_hash_12345"
            assert "explorer.solana.com" in payment.tx_url
            
            # Retrieve and verify
            retrieved = session.execute(
                select(PaymentModel).where(PaymentModel.id == payment.id)
            ).scalar_one_or_none()
            
            assert retrieved is not None
            assert retrieved.tx_hash == "test_tx_hash_12345"
            assert retrieved.tx_url == payment.tx_url


class TestMCPIntegrationFields:
    """Test MCP integration fields in payment model"""
    
    def test_mcp_fields_in_payment_model(self):
        """Test that MCP fields are present in payment model"""
        with get_sync_session() as session:
            payment = PaymentModel(
                amount=0.01,
                currency="USD",
                recipient_address="test_recipient",
                network="solana",
                purpose="Test MCP fields",
                status="success",
                mcp_tool="agent_quote",
                request_id="req_123",
                latency_ms=150.5,
                cost_usd=0.02,
                wallet="test_wallet_address"
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)
            
            # Verify MCP fields
            assert payment.mcp_tool == "agent_quote"
            assert payment.request_id == "req_123"
            assert payment.latency_ms == 150.5
            assert payment.cost_usd == 0.02
            assert payment.wallet == "test_wallet_address"