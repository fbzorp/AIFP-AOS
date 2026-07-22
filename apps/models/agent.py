from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base

class AgentModel(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: "agent-" + str(uuid4()))
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default="active")
    tools = Column(JSON)
    inputs = Column(JSON)
    outputs = Column(JSON)
    policies = Column(JSON)
    kpis = Column(JSON)
    execution_history = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())