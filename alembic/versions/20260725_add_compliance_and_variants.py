"""add compliance and variants

Revision ID: 20260725_compliance
Revises: 7ff8e3bbcdfd
Create Date: 2026-07-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260725_compliance'
down_revision = '7ff8e3bbcdfd'
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
