"""add payments table

Revision ID: 20260729_add_payments
Revises: 20260726_days_10_11
Create Date: 2026-07-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260729_add_payments'
down_revision = '20260726_days_10_11'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'payments',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('recipient_address', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default='USDC'),
        sa.Column('network', sa.String(), nullable=False, server_default='solana'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('tx_hash', sa.String(), nullable=True),
        sa.Column('tx_url', sa.String(), nullable=True),
        sa.Column('x402_request_url', sa.String(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('payments')
