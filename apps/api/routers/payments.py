from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
import logging
import time

from apps.models.base import get_db
from apps.models.payment import PaymentModel
from apps.models.audit_event import AuditEventModel
from apps.schemas.payment import PaymentCreate, PaymentResponse, PaymentApprove, PaymentExecute
from apps.schemas.audit_event import AuditEventCreate
from apps.api.config import settings
from apps.integrations.wallet.client import WalletClient
from apps.integrations.x402.client import X402Client
from apps.integrations.aifinpay.client import AiFinPayClient
from apps.integrations.mcp.client import MCPClient
from apps.core.audit.service import record_event

router = APIRouter()
logger = logging.getLogger(__name__)

# Instantiate clients
wallet_client = WalletClient(
    solana_rpc_url=settings.SOLANA_RPC_URL,
    evm_rpc_url=settings.EVM_RPC_URL,
    solana_private_key=settings.SOLANA_PRIVATE_KEY,
    evm_private_key=settings.EVM_PRIVATE_KEY,
    per_transaction_limit=settings.PER_TRANSACTION_LIMIT,
    dry_run=(settings.PAYMENTS_NETWORK == "devnet")
)

x402_client = X402Client(
    facilitator_url=settings.X402_FACILITATOR_URL,
    wallet_client=wallet_client,
    x402_enabled=settings.X402_ENABLED,
    signing_key_base58=settings.AIFINPAY_AGENT_SECRET
)

aifinpay_client = AiFinPayClient(
    base_url=settings.AIFP_BASE_URL,
    agent_secret=settings.AIFINPAY_AGENT_SECRET,
    agent_pubkey=settings.AIFINPAY_AGENT_PUBKEY,
    dry_run=(settings.PAYMENTS_NETWORK == "devnet")
)

mcp_client = MCPClient(
    mcp_server_url="http://aifinpay-mcp:3000",
    max_usd=settings.AIFINPAY_MAX_USD,
    enabled=settings.AIFINPAY_MCP_ENABLED
)

async def create_audit_event(db: AsyncSession, event_type: str, details: dict):
    audit_event = AuditEventModel(
        agent_name="System",
        event_type=event_type,
        message=f"Payment event: {event_type}",
        metadata_json=details
    )
    db.add(audit_event)
    await db.commit()
    await db.refresh(audit_event)
    return audit_event

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_in: PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    # Emergency Kill Switch check
    if settings.PAYMENTS_KILL_SWITCH:
        await create_audit_event(db, "payment_rejected_kill_switch", {"purpose": payment_in.purpose, "amount": payment_in.amount})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payments are currently disabled via emergency kill switch")

    # Recipient Allowlist check
    if settings.RECIPIENT_ALLOWLIST:
        allowed_recipients = [r.strip() for r in settings.RECIPIENT_ALLOWLIST.split(",")]
        if payment_in.recipient_address not in allowed_recipients:
            await create_audit_event(db, "payment_rejected_not_allowlisted", {"recipient": payment_in.recipient_address, "amount": payment_in.amount})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recipient address is not in the allowlist")

    status_to_set = "pending"
    if payment_in.amount <= settings.HUMAN_APPROVAL_THRESHOLD:
        status_to_set = "approved"

    payment = PaymentModel(**payment_in.model_dump(), status=status_to_set)
    
    if settings.X402_ENABLED:
        try:
            payment.x402_request_url = await x402_client.create_payment_request(
                amount=payment.amount,
                currency=payment.currency,
                purpose=payment.purpose
            )
        except Exception as e:
            logger.warning(f"X402 request generation failed: {e}")

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    await create_audit_event(db, "payment_requested", {"payment_id": payment.id, "amount": payment.amount, "currency": payment.currency, "status": status_to_set})

    return payment

@router.post("/{payment_id}/approve", response_model=PaymentResponse)
async def approve_payment(
    payment_id: str,
    payment_approve: PaymentApprove,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not in pending status")

    # Enforce per-transaction limit
    if payment.amount > settings.PER_TRANSACTION_LIMIT:
        await create_audit_event(db, "payment_approval_denied", {"payment_id": payment.id, "reason": "Exceeds per-transaction limit"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment exceeds per-transaction limit")

    # Enforce daily spending limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_spend_query = select(func.sum(PaymentModel.amount)).filter(
        PaymentModel.created_at >= today_start,
        PaymentModel.status.in_(["approved", "executing", "success"])
    )
    current_daily_spend = (await db.execute(daily_spend_query)).scalar() or 0
    if current_daily_spend + payment.amount > settings.DAILY_SPENDING_LIMIT:
        await create_audit_event(db, "payment_approval_denied", {"payment_id": payment.id, "reason": "Exceeds daily spending limit"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment exceeds daily spending limit")

    payment.status = "approved"
    payment.approved_by = payment_approve.approved_by
    await db.commit()
    await db.refresh(payment)

    await create_audit_event(db, "payment_approved", {"payment_id": payment.id, "approved_by": payment_approve.approved_by})

    return payment

@router.post("/{payment_id}/execute", response_model=PaymentResponse)
async def execute_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Emergency Kill Switch check
    if settings.PAYMENTS_KILL_SWITCH:
        await create_audit_event(db, "payment_execution_denied_kill_switch", {"payment_id": payment_id})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payments are currently disabled via emergency kill switch")

    result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not in approved status")

    payment.status = "executing"
    await db.commit()

    try:
        start_time = time.time()
        
        # Use AiFinPay client to create invoice if available
        if settings.AIFINPAY_AGENT_SECRET and settings.AIFINPAY_AGENT_PUBKEY:
            try:
                invoice = await aifinpay_client.create_invoice(
                    amount=payment.amount,
                    currency=payment.currency,
                    network=payment.network
                )
                logger.info(f"Created AiFinPay invoice: {invoice}")
                payment.mcp_tool = "create_invoice"
                payment.request_id = invoice.get("id", "unknown")
            except Exception as e:
                logger.warning(f"AiFinPay invoice creation failed, falling back to direct wallet: {e}")
        
        # Execute transaction via wallet client
        tx_hash = await wallet_client.send_transaction(
            network=payment.network,
            amount=payment.amount,
            recipient_address=payment.recipient_address,
            force_real=True  # Force real execution
        )
        
        tx_url = "https://explorer.example.com"
        if payment.network == "solana":
            tx_url = f"https://explorer.solana.com/tx/{tx_hash}?cluster=devnet"
        elif payment.network == "evm":
            tx_url = f"https://sepolia.basescan.org/tx/{tx_hash}"

        # Calculate latency and cost
        latency_ms = (time.time() - start_time) * 1000
        cost_usd = payment.amount  # Simplified cost calculation
        
        payment.status = "success"
        payment.tx_hash = tx_hash
        payment.tx_url = tx_url
        payment.latency_ms = latency_ms
        payment.cost_usd = cost_usd
        # Get wallet address
        if payment.network == "solana" and wallet_client._solana_keypair:
            payment.wallet = str(wallet_client._solana_keypair.pubkey())
        elif payment.network == "evm" and wallet_client._evm_account:
            payment.wallet = wallet_client._evm_account.address
        await db.commit()
        await db.refresh(payment)

        await create_audit_event(db, "payment_executed", {
            "payment_id": payment.id, 
            "tx_hash": tx_hash, 
            "explorer_url": tx_url,
            "status": "success",
            "wallet": payment.wallet,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "mcp_tool": payment.mcp_tool,
            "request_id": payment.request_id
        })

    except Exception as e:
        payment.status = "failed"
        payment.error = str(e)
        await db.commit()
        await db.refresh(payment)
        await create_audit_event(db, "payment_execution_failed", {"payment_id": payment.id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment execution failed: {e}")

    return payment

@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PaymentModel).order_by(PaymentModel.created_at.desc()).offset(skip).limit(limit))
    payments = result.scalars().all()
    return payments
