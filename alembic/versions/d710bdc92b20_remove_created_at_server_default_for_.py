"""remove_created_at_server_default_for_audit_hash

Revision ID: d710bdc92b20
Revises: 20260811_add_audit_integrity
Create Date: 2026-08-12 03:55:44.392869

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func, text, text, text


# revision identifiers, used by Alembic.
revision = 'd710bdc92b20'
down_revision = '20260811_add_audit_integrity'
branch_labels = None
depends_on = None


def upgrade():
    # Remove server_default from created_at to enable Python-side timestamp for hash computation
    # This is needed to compute record_hash before INSERT (avoiding UPDATE that triggers append-only protection)
    # Check if table exists first (in case this is a fresh database)
    conn = op.get_bind()
    is_postgres = conn.dialect.name == 'postgresql'
    
    if is_postgres:
        # Check if audit_events table exists
        table_exists = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'audit_events'
            )
        """)).scalar()
        
        if table_exists:
            op.alter_column('audit_events', 'created_at', existing_type=sa.DateTime(timezone=True), nullable=False, server_default=None)


def downgrade():
    # Restore server_default for created_at (only if table exists)
    conn = op.get_bind()
    is_postgres = conn.dialect.name == 'postgresql'
    
    if is_postgres:
        table_exists = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'audit_events'
            )
        """)).scalar()
        
        if table_exists:
            op.alter_column('audit_events', 'created_at', existing_type=sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
