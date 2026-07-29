"""Add MCP integration fields to payments table

Revision ID: 001_add_mcp_fields
Revises: 
Create Date: 2026-07-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_mcp_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add MCP integration fields to payments table
    op.add_column('payments', sa.Column('mcp_tool', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('request_id', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('latency_ms', sa.Float(), nullable=True))
    op.add_column('payments', sa.Column('cost_usd', sa.Float(), nullable=True))
    op.add_column('payments', sa.Column('wallet', sa.String(), nullable=True))
    
    # Make recipient_address mandatory
    op.alter_column('payments', 'recipient_address', nullable=False)


def downgrade():
    # Remove MCP integration fields
    op.drop_column('payments', 'wallet')
    op.drop_column('payments', 'cost_usd')
    op.drop_column('payments', 'latency_ms')
    op.drop_column('payments', 'request_id')
    op.drop_column('payments', 'mcp_tool')
    
    # Make recipient_address optional again
    op.alter_column('payments', 'recipient_address', nullable=True)