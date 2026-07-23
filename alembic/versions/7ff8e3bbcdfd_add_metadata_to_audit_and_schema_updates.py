"""add_metadata_to_audit_and_schema_updates

Revision ID: 7ff8e3bbcdfd
Revises: 20260723_create_tasks_table
Create Date: 2026-07-23 17:35:51.050710

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ff8e3bbcdfd'
down_revision = '20260723_create_tasks_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add metadata_json to audit_events
    op.add_column('audit_events', sa.Column('metadata_json', sa.JSON(), nullable=True))
    
    # Create campaigns table if it doesn't exist (it might be in foundation but let's be sure)
    # Check if table exists first is better but Alembic usually handles it via its own state
    # Actually, let's create the ApprovalModel table as requested
    op.create_table(
        'approvals',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('draft_hash', sa.String(), nullable=False),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('approvals')
    op.drop_column('audit_events', 'metadata_json')
