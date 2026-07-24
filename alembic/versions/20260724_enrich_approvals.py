"""enrich_approvals

Revision ID: 20260724_enrich_approvals
Revises: e97c7449d888
Create Date: 2026-07-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260724_enrich_approvals'
down_revision = 'e97c7449d888'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to approvals table
    op.add_column('approvals', sa.Column('content_id', sa.String(), nullable=True))
    op.add_column('approvals', sa.Column('status', sa.String(), server_default='pending', nullable=False))
    op.add_column('approvals', sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create index for content_id
    op.create_index(op.f('ix_approvals_content_id'), 'approvals', ['content_id'], unique=False)


def downgrade():
    # Remove columns and index
    op.drop_index(op.f('ix_approvals_content_id'), table_name='approvals')
    op.drop_column('approvals', 'decided_at')
    op.drop_column('approvals', 'status')
    op.drop_column('approvals', 'content_id')
