import logging
from sqlalchemy.orm import Session
from apps.models.audit_event import AuditEventModel

logger = logging.getLogger(__name__)

def record_event(session: Session, agent_name: str, event_type: str, message: str, metadata: dict = None):
    """
    Records an audit event to the database.
    """
    try:
        event = AuditEventModel(
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            metadata_json=metadata
        )
        session.add(event)
        session.flush()  # Ensure it's ready but don't commit yet (caller manages transaction)
        logger.info(f"Audit: [{agent_name}] {event_type} - {message}")
    except Exception as e:
        logger.error(f"Failed to record audit event: {e}")
