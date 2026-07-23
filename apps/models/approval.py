from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class ApprovalModel(Base):
    __tablename__ = "approvals"
    
    id = Column(String, primary_key=True, default=lambda: "appr-" + str(uuid4()))
    draft_hash = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
