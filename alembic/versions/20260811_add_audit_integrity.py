"""add_audit_integrity

Revision ID: 20260811_add_audit_integrity
Revises: 47c43b9c29dc
Create Date: 2026-08-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import hashlib
import json
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260811_add_audit_integrity'
down_revision = '47c43b9c29dc'
branch_labels = None
depends_on = None


def _canonical_json(metadata):
    """Convert metadata to canonical JSON string for deterministic hashing."""
    if metadata is None:
        return ""
    return json.dumps(metadata, sort_keys=True, separators=(',', ':'))


def _compute_record_hash(prev_hash, id, agent_name, event_type, message, metadata_json, created_at):
    """Compute SHA256 hash for an audit record."""
    created_at_iso = created_at.isoformat() if created_at else ""
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


def upgrade():
    # Add integrity columns to audit_events table
    # Add prev_hash as nullable (for genesis row)
    op.add_column('audit_events', sa.Column('prev_hash', sa.String(), nullable=True))
    # Add record_hash as nullable (hash computed after INSERT)
    op.add_column('audit_events', sa.Column('record_hash', sa.String(), nullable=True))
    
    # Backfill existing records with hash chain
    # Get the database connection
    conn = op.get_bind()
    
    # Check if we're using PostgreSQL (for trigger creation)
    is_postgres = conn.dialect.name == 'postgresql'
    
    # Backfill hashes for existing records using Python-side computation
    # This approach is portable and doesn't require pgcrypto extension
    result = conn.execute(sa.text("""
        SELECT id, agent_name, event_type, message, metadata_json, created_at
        FROM audit_events
        ORDER BY created_at, id
    """))
    
    events = result.fetchall()
    prev_hash = None
    
    for event in events:
        event_id, agent_name, event_type, message, metadata_json, created_at = event
        
        # Compute hash using Python
        record_hash = _compute_record_hash(
            prev_hash=prev_hash,
            id=event_id,
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            metadata_json=metadata_json,
            created_at=created_at
        )
        
        # Update the record
        conn.execute(sa.text("""
            UPDATE audit_events
            SET prev_hash = :prev_hash,
                record_hash = :record_hash
            WHERE id = :id
        """), {
            'prev_hash': prev_hash,
            'record_hash': record_hash,
            'id': event_id
        })
        
        prev_hash = record_hash
    
    # Create PostgreSQL trigger for append-only enforcement
    if is_postgres:
        # Create trigger function to prevent UPDATE and DELETE
        conn.execute(sa.text("""
            CREATE OR REPLACE FUNCTION prevent_audit_modification()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'Audit events are append-only. Modification (UPDATE/DELETE) is not allowed.';
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        # Create trigger for UPDATE
        conn.execute(sa.text("""
            CREATE TRIGGER audit_events_prevent_update
            BEFORE UPDATE ON audit_events
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_modification();
        """))
        
        # Create trigger for DELETE
        conn.execute(sa.text("""
            CREATE TRIGGER audit_events_prevent_delete
            BEFORE DELETE ON audit_events
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_modification();
        """))


def downgrade():
    conn = op.get_bind()
    is_postgres = conn.dialect.name == 'postgresql'
    
    # Drop PostgreSQL triggers if they exist
    if is_postgres:
        try:
            conn.execute(sa.text("DROP TRIGGER IF EXISTS audit_events_prevent_update ON audit_events"))
            conn.execute(sa.text("DROP TRIGGER IF EXISTS audit_events_prevent_delete ON audit_events"))
            conn.execute(sa.text("DROP FUNCTION IF EXISTS prevent_audit_modification()"))
        except Exception:
            pass
    
    # Drop integrity columns
    op.drop_column('audit_events', 'record_hash')
    op.drop_column('audit_events', 'prev_hash')