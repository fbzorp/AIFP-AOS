from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from .base import Base


class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True,
                default=lambda: "agent-" + str(func.uuid()))
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        onupdate=func.now(), server_default=func.now())
