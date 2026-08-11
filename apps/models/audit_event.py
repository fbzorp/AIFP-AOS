from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from uuid import uuid4

from .base import Base


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True,
                default=lambda: "audit-" + str(uuid4()))
    agent_name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Renamed to avoid conflict with Base.metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Integrity fields for tamper-resistant audit chain
    # prev_hash: Hash of the previous record's record_hash (NULL for genesis row)
    prev_hash = Column(String, nullable=True)
    # record_hash: SHA256 hash of (prev_hash + id + agent_name + event_type + message + canonical_json(metadata_json) + created_at_iso)
    record_hash = Column(String, nullable=True)  # Made nullable to allow hash computation after INSERT