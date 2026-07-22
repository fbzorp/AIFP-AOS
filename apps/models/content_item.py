from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from uuid import uuid4

from .base import Base


class ContentItemModel(Base):
    __tablename__ = "content_items"

    id = Column(String, primary_key=True,
                default=lambda: "content-" + str(uuid4()))
    title = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")
    body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        onupdate=func.now(), server_default=func.now())