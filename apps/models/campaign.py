from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from .base import Base


class CampaignModel(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True,
                default=lambda: "campaign-" + str(func.uuid()))
    name = Column(String, nullable=False)
    objective = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        onupdate=func.now(), server_default=func.now())
