"""add compliance and variants

Revision ID: 20260725_compliance
Revises: e97c7449d888
Create Date: 2026-07-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260725_compliance'
down_revision = 'e97c7449d888'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('content_items', sa.Column('variants', sa.JSON(), nullable=True))
    op.add_column('content_items', sa.Column('compliance_status', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('compliance_reason', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('content_items', 'compliance_reason')
    op.drop_column('content_items', 'compliance_status')
    op.drop_column('content_items', 'variants')
