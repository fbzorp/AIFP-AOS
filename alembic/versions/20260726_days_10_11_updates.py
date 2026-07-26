"""Days 10-11 updates: publication fields and engagement proposals

Revision ID: 20260726_days_10_11
Revises: 20260725_compliance
Create Date: 2026-07-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260726_days_10_11'
down_revision = '20260725_compliance'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add publication and scheduling columns to content_items
    op.add_column('content_items', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('content_items', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('content_items', sa.Column('post_url', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('post_id', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('publish_error', sa.Text(), nullable=True))

    # 2. Create engagement_proposals table
    op.create_table(
        'engagement_proposals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('submolt', sa.String(), nullable=False),
        sa.Column('discussion_summary', sa.Text(), nullable=False),
        sa.Column('proposed_reply', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='proposed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # 1. Drop engagement_proposals table
    op.drop_table('engagement_proposals')

    # 2. Remove publication and scheduling columns from content_items
    op.drop_column('content_items', 'publish_error')
    op.drop_column('content_items', 'post_id')
    op.drop_column('content_items', 'post_url')
    op.drop_column('content_items', 'published_at')
    op.drop_column('content_items', 'scheduled_at')
