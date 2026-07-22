from sqlalchemy import Column, String, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class AgentModel(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    tools = Column(JSON)
    inputs = Column(JSON)
    outputs = Column(JSON)
    policies = Column(JSON)
    kpis = Column(JSON)
    execution_history = Column(JSON)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
# Similar fixes for campaign.py and content_item.py with UUID defaults
