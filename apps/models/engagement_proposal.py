from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class EngagementProposalModel(Base):
    __tablename__ = "engagement_proposals"

    id = Column(String, primary_key=True, default=lambda: "engage-" + str(uuid4()))
    source_url = Column(String, nullable=False)
    submolt = Column(String, nullable=False)
    discussion_summary = Column(Text, nullable=False)
    proposed_reply = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="proposed") # proposed, approved, rejected, posted
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<EngagementProposal(id={self.id}, status={self.status}, submolt={self.submolt})>"
