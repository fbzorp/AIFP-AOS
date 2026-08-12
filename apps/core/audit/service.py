import logging
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apps.models.audit_event import AuditEventModel

logger = logging.getLogger(__name__)


def _canonical_json(metadata: dict) -> str:
    """
    Convert metadata to canonical JSON string for deterministic hashing.
    Sorts keys and uses consistent formatting.
    """
    if metadata is None:
        return ""
    return json.dumps(metadata, sort_keys=True, separators=(',', ':'))


def _compute_record_hash(prev_hash: str, id: str, agent_name: str, event_type: str, 
                        message: str, metadata_json: dict, created_at: datetime) -> str:
    """
    Compute SHA256 hash for an audit record.
    
    Hash = sha256(prev_hash + id + agent_name + event_type + message + canonical_json(metadata_json) + created_at_iso)
    
    Args:
        prev_hash: Hash of previous record (empty string for genesis row)
        id: Record ID
        agent_name: Agent name
        event_type: Event type
        message: Event message
        metadata_json: Metadata dictionary
        created_at: Creation timestamp
    
    Returns:
        Hexadecimal SHA256 hash
    """
    # Convert created_at to ISO format string for deterministic hashing
    created_at_iso = created_at.isoformat() if created_at else ""
    
    # Build hash input with all fields
    hash_input = (
        str(prev_hash) +
        str(id) +
        str(agent_name) +
        str(event_type) +
        str(message) +
        _canonical_json(metadata_json) +
        created_at_iso
    )
    
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def record_event(session, agent_name: str, event_type: str, message: str, metadata: dict = None):
    """
    Records an audit event to the database with tamper-resistant hash chaining.
    
    Hash Chain Logic:
    1. Look up the most recent existing audit row's record_hash (ordered by created_at, then id)
    2. Set it as prev_hash (NULL for genesis row)
    3. Set created_at explicitly in Python (not DB default) to enable pre-INSERT hash computation
    4. Compute record_hash using SHA256(prev_hash + id + agent_name + event_type + message + canonical_json(metadata) + created_at_iso)
    5. Persist the record in a single INSERT (no UPDATE to avoid append-only trigger)
    
    Concurrent Insert Handling:
    - This function assumes a single-writer model (sequential insert ordering)
    - The SELECT for prev_hash happens before INSERT to maintain chain integrity
    - In concurrent scenarios, the race condition could cause chain breaks
    - Document assumption: Audit writes are serialized in production
    
    Uses sync session for database operations.
    """
    # Get the most recent audit event's record_hash for chaining
    # Order by created_at, then id for deterministic ordering
    prev_hash = None
    try:
        result = session.execute(
            select(AuditEventModel.record_hash)
            .order_by(desc(AuditEventModel.created_at), desc(AuditEventModel.id))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            prev_hash = row
    except Exception as e:
        # If table doesn't exist or other DB error, log and continue
        # This allows graceful degradation in test environments
        logger.warning(f"Could not fetch prev_hash for audit chain: {e}")
        # Continue without prev_hash (will be genesis row or broken chain)
    
    # Set created_at explicitly in Python to enable pre-INSERT hash computation
    created_at = datetime.now(timezone.utc)
    
    # Generate ID explicitly to have all fields before INSERT
    event_id = "audit-" + str(uuid4())
    
    # Compute record_hash BEFORE INSERT to avoid UPDATE (which triggers append-only protection)
    record_hash = _compute_record_hash(
        prev_hash=prev_hash,
        id=event_id,
        agent_name=agent_name,
        event_type=event_type,
        message=message,
        metadata_json=metadata,
        created_at=created_at
    )
    
    # Create the audit event with all fields populated
    event = AuditEventModel(
        id=event_id,
        agent_name=agent_name,
        event_type=event_type,
        message=message,
        metadata_json=metadata,
        prev_hash=prev_hash,
        record_hash=record_hash,
        created_at=created_at
    )
    
    # Single INSERT with all fields (no UPDATE needed)
    session.add(event)
    session.flush()
    
    logger.info(f"Audit: [{agent_name}] {event_type} - {message}")
    return event


async def record_event_async(session: AsyncSession, agent_name: str, event_type: str, 
                            message: str, metadata: dict = None):
    """
    Async version of record_event for use with AsyncSession.
    
    Ensures proper hash chaining with async database operations.
    Computes hash before INSERT to avoid UPDATE (which triggers append-only protection).
    """
    # Get the most recent audit event's record_hash for chaining
    prev_hash = None
    try:
        result = await session.execute(
            select(AuditEventModel.record_hash)
            .order_by(desc(AuditEventModel.created_at), desc(AuditEventModel.id))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            prev_hash = row
    except Exception as e:
        # If table doesn't exist or other DB error, log and continue
        logger.warning(f"Could not fetch prev_hash for audit chain: {e}")
        # Continue without prev_hash (will be genesis row or broken chain)
    
    # Set created_at explicitly in Python to enable pre-INSERT hash computation
    created_at = datetime.now(timezone.utc)
    
    # Generate ID explicitly to have all fields before INSERT
    event_id = "audit-" + str(uuid4())
    
    # Compute record_hash BEFORE INSERT to avoid UPDATE (which triggers append-only protection)
    record_hash = _compute_record_hash(
        prev_hash=prev_hash,
        id=event_id,
        agent_name=agent_name,
        event_type=event_type,
        message=message,
        metadata_json=metadata,
        created_at=created_at
    )
    
    # Create the audit event with all fields populated
    event = AuditEventModel(
        id=event_id,
        agent_name=agent_name,
        event_type=event_type,
        message=message,
        metadata_json=metadata,
        prev_hash=prev_hash,
        record_hash=record_hash,
        created_at=created_at
    )
    
    # Single INSERT with all fields (no UPDATE needed)
    session.add(event)
    await session.flush()
    
    logger.info(f"Audit: [{agent_name}] {event_type} - {message}")
    return event


def verify_audit_chain(session) -> dict:
    """
    Verify the integrity of the audit event chain by recomputing hashes.
    
    Walks through rows in order (created_at, then id) and recomputes each record_hash
    from stored fields + the previous prev_hash.
    
    Args:
        session: Database session (sync Session)
    
    Returns:
        Dict with:
        - valid: Boolean indicating if chain is intact
        - first_broken_id: ID of first broken record (None if valid)
        - total_records: Total number of records checked
        - broken_records: Number of broken records found
    """
    try:
        # Get all audit events ordered by created_at, then id
        result = session.execute(
            select(AuditEventModel)
            .order_by(AuditEventModel.created_at, AuditEventModel.id)
        )
        events = result.scalars().all()
        
        if not events:
            return {
                "valid": True,
                "first_broken_id": None,
                "total_records": 0,
                "broken_records": 0
            }
        
        broken_count = 0
        first_broken_id = None
        expected_prev_hash = None  # Genesis row should have prev_hash = None
        
        for event in events:
            # Verify prev_hash matches expected
            if event.prev_hash != expected_prev_hash:
                broken_count += 1
                if first_broken_id is None:
                    first_broken_id = event.id
                logger.error(f"Chain break at record {event.id}: expected prev_hash={expected_prev_hash}, got={event.prev_hash}")
                # Continue checking to find all breaks
                expected_prev_hash = event.record_hash  # Still expect next record to chain from this one
                continue
            
            # Recompute record_hash and verify
            computed_hash = _compute_record_hash(
                prev_hash=event.prev_hash,
                id=event.id,
                agent_name=event.agent_name,
                event_type=event.event_type,
                message=event.message,
                metadata_json=event.metadata_json,
                created_at=event.created_at
            )
            
            if computed_hash != event.record_hash:
                broken_count += 1
                if first_broken_id is None:
                    first_broken_id = event.id
                logger.error(f"Hash mismatch at record {event.id}: expected={computed_hash}, got={event.record_hash}")
            
            # Set expected prev_hash for next record
            expected_prev_hash = event.record_hash
        
        return {
            "valid": broken_count == 0,
            "first_broken_id": first_broken_id,
            "total_records": len(events),
            "broken_records": broken_count
        }
        
    except Exception as e:
        logger.error(f"Failed to verify audit chain: {e}")
        return {
            "valid": False,
            "first_broken_id": None,
            "total_records": 0,
            "broken_records": 0,
            "error": str(e)
        }
