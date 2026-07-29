from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaymentBase(BaseModel):
    purpose: str
    recipient_address: str
    amount: float
    currency: str = "USDC"
    network: str = "solana"

class PaymentCreate(PaymentBase):
    pass

class PaymentApprove(BaseModel):
    approved_by: str

class PaymentExecute(BaseModel):
    pass

class PaymentResponse(PaymentBase):
    id: str
    status: str
    tx_hash: Optional[str] = None
    tx_url: Optional[str] = None
    x402_request_url: Optional[str] = None
    recipient_address: str
    approved_by: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
