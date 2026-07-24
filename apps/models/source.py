import uuid
from sqlalchemy import Column, String, Text, Float, DateTime, func
from .base import Base

class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=lambda: "source-" + str(uuid.uuid4()))
    url = Column(String, unique=True, nullable=False)
    url_hash = Column(String, index=True, nullable=False)
    
    title = Column(String)
    author = Column(String)
    published_date = Column(DateTime)
    
    summary = Column(Text)
    relevance_score = Column(Float, default=0.0)
    content_angle = Column(Text)
    topic = Column(String)
    
    raw_content = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Source(id={self.id}, url={self.url}, topic={self.topic})>"
