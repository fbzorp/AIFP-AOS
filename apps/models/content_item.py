from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class ContentItemModel(Base):
    __tablename__ = "content_items"

    id = Column(String, primary_key=True, default=lambda: "content-" + str(uuid4()))
    title = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")
    body = Column(Text, nullable=True)
    variants = Column(JSON, nullable=True)
    
    # Compliance
    compliance_status = Column(String, nullable=True)
    compliance_reason = Column(Text, nullable=True)
    
    # Technical Verification
    technical_verification_status = Column(String, nullable=True)  # 'verified', 'failed', 'pending', 'flagged'
    technical_verification_details = Column(Text, nullable=True)  # Details of verification check
    
    # Strategy & Attribution
    objective = Column(Text)
    target_audience = Column(String)
    format = Column(String)
    cta = Column(String)
    kpi = Column(String)
    
    source_id = Column(String, index=True) # Soft reference or FK
    author_agent = Column(String)
    
    # Publication & Calendar
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    post_url = Column(String, nullable=True)
    post_id = Column(String, nullable=True)
    publish_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<ContentItem(id={self.id}, title={self.title}, status={self.status})>"
