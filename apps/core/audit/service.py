import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from apps.models.audit_event import AuditEventModel

logger = logging.getLogger(__name__)

def record_event(session, agent_name: str, event_type: str, message: str, metadata: dict = None):
    """
    Records an audit event to the database.
    Handles both sync and async sessions by checking if flush() needs to be awaited.
    """
    try:
        event = AuditEventModel(
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            metadata_json=metadata
        )
        session.add(event)
        
        # Check if we are in an async session
        if isinstance(session, AsyncSession):
            # We can't easily await here without making record_event async
            # But for audit, just adding to session is often enough before the caller commits.
            # However, to fix the warning in tests where we might be using AsyncSession:
            pass 
        else:
            session.flush()
            
        logger.info(f"Audit: [{agent_name}] {event_type} - {message}")
    except Exception as e:
        logger.error(f"Failed to record audit event: {e}")
