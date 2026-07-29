from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import logging

from apps.models.base import get_db
from apps.models.payment import PaymentModel
from apps.models.audit_event import AuditEventModel
from apps.schemas.payment import PaymentCreate, PaymentResponse, PaymentApprove, PaymentExecute
from apps.schemas.audit_event import AuditEventCreate
from apps.api.config import settings
from apps.integrations.wallet.client import WalletClient
from apps.integrations.x402.client import X402Client
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
    x402_enabled=settings.X402_ENABLED
)

async def create_audit_event(db: AsyncSession, event_type: str, details: dict):
    # Use the existing AuditEventModel but handle metadata_json correctly
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
    status_to_set = "pending"
    if payment_in.amount <= settings.HUMAN_APPROVAL_THRESHOLD:
        status_to_set = "approved"

    payment = PaymentModel(**payment_in.model_dump(), status=status_to_set)
    
    # Generate X402 request URL if enabled
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
    result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not in approved status")

    payment.status = "executing"
    await db.commit()

    try:
        tx_result = await wallet_client.transfer(
            network=payment.network,
            to_address="recipient_address_placeholder", 
            amount=payment.amount,
            currency=payment.currency
        )
        payment.status = "success"
        payment.tx_hash = tx_result.get("tx_hash")
        payment.tx_url = tx_result.get("tx_url")
        await db.commit()
        await db.refresh(payment)

        await create_audit_event(db, "payment_executed", {"payment_id": payment.id, "tx_hash": payment.tx_hash, "status": "success"})

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
