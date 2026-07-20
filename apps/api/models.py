from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    agent_type = Column(String(50), nullable=False)
    model = Column(String(100), default='deepseek-chat')
    version = Column(String(20), default='0.1.0')
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    tasks = relationship('Task', back_populates='agent')
    executions = relationship('AuditLog', back_populates='agent')

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    task_type = Column(String(100), nullable=False)
    input_data = Column(Text, nullable=True)
    status = Column(String(20), default='pending')
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    agent = relationship('Agent', back_populates='tasks')

class ContentItem(Base):
    __tablename__ = 'content_items'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)
    source_url = Column(String(500), nullable=True)
    status = Column(String(50), default='draft')
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    approved_by = Column(String(100), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agent = relationship('Agent')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    action = Column(String(100), nullable=False)
    input_data = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    error = Column(Text, nullable=True)
    cost = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String(100), nullable=True)
    
    agent = relationship('Agent', back_populates='executions')