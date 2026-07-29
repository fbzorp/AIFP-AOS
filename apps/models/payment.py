from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class PaymentModel(Base):
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: "pay-" + str(uuid4()))
    purpose = Column(String, nullable=False, index=True)
    recipient_address = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USDC")
    network = Column(String, nullable=False, default="solana")
    status = Column(String, nullable=False, default="pending", index=True) # pending, approved, executing, success, failed
    tx_hash = Column(String, nullable=True)
    tx_url = Column(String, nullable=True)
    x402_request_url = Column(String, nullable=True)
    approved_by = Column(String, nullable=True) # User ID or agent ID who approved
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    # Additional fields for MCP integration
    mcp_tool = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)
    cost_usd = Column(Float, nullable=True)
    wallet = Column(String, nullable=True)
