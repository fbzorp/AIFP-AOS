from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Boolean, Integer
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
    source_urls = Column(JSON, nullable=True)  # List of source URLs for content
    author_agent = Column(String)
    
    # SEO Metadata (for SEO/page publishing)
    target_keyword = Column(String, nullable=True)
    search_intent = Column(String, nullable=True)
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    canonical_url = Column(String, nullable=True)
    indexing_status = Column(String, nullable=True)  # 'pending', 'indexed', 'not_indexed'
    internal_links = Column(JSON, nullable=True)  # List of internal links
    
    # Publication & Calendar
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)  # When human approved the content
    approver = Column(String, nullable=True)  # Who approved the content
    published_at = Column(DateTime(timezone=True), nullable=True)
    post_url = Column(String, nullable=True)
    post_id = Column(String, nullable=True)
    publish_error = Column(Text, nullable=True)
    
    # Analytics Metrics
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    engagement = Column(Integer, nullable=True)
    referrals = Column(Integer, nullable=True)
    conversions = Column(Integer, nullable=True)
    last_analytics_update = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<ContentItem(id={self.id}, title={self.title}, status={self.status})>"
