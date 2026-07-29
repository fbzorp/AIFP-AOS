from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuditEventBase(BaseModel):
    agent_name: str
    event_type: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class AuditEventCreate(AuditEventBase):
    pass

class AuditEventResponse(AuditEventBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
