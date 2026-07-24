"""add_sources_and_enrich_content_items

Revision ID: e97c7449d888
Revises: 7ff8e3bbcdfd
Create Date: 2026-07-24 08:51:45.235885

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e97c7449d888'
down_revision = '7ff8e3bbcdfd'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('url_hash', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('content_angle', sa.Text(), nullable=True),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_sources_url_hash'), 'sources', ['url_hash'], unique=False)

    # 2. Enrich content_items table
    op.add_column('content_items', sa.Column('objective', sa.Text(), nullable=True))
    op.add_column('content_items', sa.Column('target_audience', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('format', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('cta', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('kpi', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('source_id', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('author_agent', sa.String(), nullable=True))
    op.create_index(op.f('ix_content_items_source_id'), 'content_items', ['source_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_content_items_source_id'), table_name='content_items')
    op.drop_column('content_items', 'author_agent')
    op.drop_column('content_items', 'source_id')
    op.drop_column('content_items', 'kpi')
    op.drop_column('content_items', 'cta')
    op.drop_column('content_items', 'format')
    op.drop_column('content_items', 'target_audience')
    op.drop_column('content_items', 'objective')
    op.drop_index(op.f('ix_sources_url_hash'), table_name='sources')
    op.drop_table('sources')
