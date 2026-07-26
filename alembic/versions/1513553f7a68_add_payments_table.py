"""add payments table

Revision ID: 1513553f7a68
Revises: 20260726_days_10_11
Create Date: 2026-07-26 13:13:36.597147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1513553f7a68'
down_revision = '20260726_days_10_11'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('purpose', sa.String, index=True),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String, nullable=False),
        sa.Column('network', sa.String, nullable=False),
        sa.Column('status', sa.String, default='pending', index=True),
        sa.Column('tx_hash', sa.String, nullable=True),
        sa.Column('tx_url', sa.String, nullable=True),
        sa.Column('x402_request_url', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('approved_by', sa.String, nullable=True),
        sa.Column('error', sa.String, nullable=True)
    )


def downgrade():
    op.drop_table('payments')
