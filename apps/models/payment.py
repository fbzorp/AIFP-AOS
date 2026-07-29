<<<<<<< HEAD

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from apps.models.base import Base

class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    purpose = Column(String, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    network = Column(String, nullable=False)
    status = Column(String, default="pending", index=True) # pending, approved, sent, confirmed, failed
    tx_hash = Column(String, nullable=True)
    tx_url = Column(String, nullable=True)
    x402_request_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_by = Column(String, nullable=True) # User ID or agent ID who approved
    error = Column(String, nullable=True)

    # Optional: Add a relationship to an AuditEvent if needed for direct linking
    # audit_events = relationship("AuditEvent", back_populates="payment")
=======
from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class PaymentModel(Base):
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: "pay-" + str(uuid4()))
    purpose = Column(String, nullable=False)
    recipient_address = Column(String, nullable=True) # Will be mandatory after migration
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USDC")
    network = Column(String, nullable=False, default="solana")
    status = Column(String, nullable=False, default="pending") # pending, approved, executing, success, failed
    tx_hash = Column(String, nullable=True)
    tx_url = Column(String, nullable=True)
    x402_request_url = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
>>>>>>> 76e3403 (feat: implement Day 12 Part A - payments router, wallet & x402 integrations, and schemas)
