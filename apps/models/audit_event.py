from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from .base import Base


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True,
                default=lambda: "audit-" + str(func.uuid()))
    agent_name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
