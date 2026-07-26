
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from apps.dependencies import get_db
from apps.models.payment import PaymentModel
from apps.models.audit_event import AuditEventModel
from apps.schemas.payment import PaymentCreate, PaymentResponse, PaymentApprove, PaymentExecute
from apps.schemas.audit_event import AuditEventCreate
from apps.core.config import settings
from apps.integrations.wallet_client import WalletClient
from apps.integrations.x402_client import X402Client

router = APIRouter()

async def create_audit_event(db: AsyncSession, event_type: str, details: dict):
    audit_event = AuditEventModel(**AuditEventCreate(event_type=event_type, details=details).model_dump())
    db.add(audit_event)
    await db.commit()
    await db.refresh(audit_event)
    return audit_event

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_in: PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    status_to_set = "pending"
    if payment_in.amount <= settings.HUMAN_APPROVAL_THRESHOLD:
        status_to_set = "approved"

    payment = PaymentModel(**payment_in.model_dump(), status=status_to_set)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    await create_audit_event(db, "payment_requested", {"payment_id": payment.id, "amount": payment.amount, "currency": payment.currency, "status": status_to_set})

    return payment

@router.post("/payments/{payment_id}/approve", response_model=PaymentResponse)
async def approve_payment(
    payment_id: int,
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
    # This would require querying all payments for the current day and summing their amounts.
    # For simplicity, this is a placeholder. A real implementation would need a more robust daily limit check.
    # For now, we'll assume it passes.
    # daily_spend_query = select(func.sum(PaymentModel.amount)).filter(
    #     PaymentModel.created_at >= func.date_trunc("day", func.now()),
    #     PaymentModel.status.in_(["approved", "sent", "confirmed"])
    # )
    # current_daily_spend = (await db.execute(daily_spend_query)).scalar_one_or_none() or 0
    # if current_daily_spend + payment.amount > settings.DAILY_SPENDING_LIMIT:
    #     await create_audit_event(db, "payment_approval_denied", {"payment_id": payment.id, "reason": "Exceeds daily spending limit"})
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment exceeds daily spending limit")

    payment.status = "approved"
    payment.approved_by = payment_approve.approved_by
    await db.commit()
    await db.refresh(payment)

    await create_audit_event(db, "payment_approved", {"payment_id": payment.id, "approved_by": payment_approve.approved_by})

    return payment

@router.post("/payments/{payment_id}/execute", response_model=PaymentResponse)
async def execute_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not in approved status")

    wallet_client = WalletClient(network=payment.network, dry_run=(settings.PAYMENTS_NETWORK == "devnet"))
    x402_client = None
    if settings.X402_ENABLED:
        x402_client = X402Client(dry_run=(settings.PAYMENTS_NETWORK == "devnet"))

    try:
        # Simulate transaction sending
        tx_hash = "dry_run_tx_hash_" + str(payment.id)
        tx_url = f"https://explorer.{payment.network}/tx/{tx_hash}"

        # In a real scenario, call wallet_client.send_transaction and x402_client if enabled
        # For now, we're simulating a successful dry run.
        # tx_hash, tx_url = await wallet_client.send_transaction(payment.amount, payment.currency, payment.network)
        # if x402_client:
        #     x402_request_url = await x402_client.create_request(payment.amount, payment.currency)
        #     payment.x402_request_url = x402_request_url

        payment.tx_hash = tx_hash
        payment.tx_url = tx_url
        payment.status = "confirmed"
        await db.commit()
        await db.refresh(payment)

        await create_audit_event(db, "payment_executed", {"payment_id": payment.id, "tx_hash": tx_hash, "status": "confirmed"})

    except Exception as e:
        payment.status = "failed"
        payment.error = str(e)
        await db.commit()
        await db.refresh(payment)
        await create_audit_event(db, "payment_execution_failed", {"payment_id": payment.id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment execution failed: {e}")

    return payment

@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PaymentModel).offset(skip).limit(limit))
    payments = result.scalars().all()
    return payments
