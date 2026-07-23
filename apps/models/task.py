from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from uuid import uuid4

from .base import Base


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True,
                default=lambda: "task-" + str(uuid4()))
    agent_id = Column(String, nullable=True)
    task_type = Column(String, nullable=False)
    input_data = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        onupdate=func.now(), server_default=func.now())
