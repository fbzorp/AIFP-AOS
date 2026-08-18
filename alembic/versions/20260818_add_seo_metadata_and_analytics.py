"""Add SEO metadata and analytics columns to content_items

Revision ID: 20260818_add_seo_metadata_and_analytics
Revises: 7ff8e3bbcdfd
Create Date: 2026-08-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260818_add_seo_metadata_and_analytics'
down_revision = '7ff8e3bbcdfd'
branch_labels = None
depends_on = None


def upgrade():
    # Add approved_at and approver columns for approval tracking
    op.add_column('content_items', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('content_items', sa.Column('approver', sa.String(), nullable=True))
    
    # Add SEO metadata columns
    op.add_column('content_items', sa.Column('source_urls', sa.JSON(), nullable=True))
    op.add_column('content_items', sa.Column('target_keyword', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('search_intent', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('meta_title', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('meta_description', sa.Text(), nullable=True))
    op.add_column('content_items', sa.Column('canonical_url', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('indexing_status', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('internal_links', sa.JSON(), nullable=True))
    
    # Add analytics columns
    op.add_column('content_items', sa.Column('impressions', sa.Integer(), nullable=True))
    op.add_column('content_items', sa.Column('clicks', sa.Integer(), nullable=True))
    op.add_column('content_items', sa.Column('engagement', sa.Integer(), nullable=True))
    op.add_column('content_items', sa.Column('referrals', sa.Integer(), nullable=True))
    op.add_column('content_items', sa.Column('conversions', sa.Integer(), nullable=True))
    op.add_column('content_items', sa.Column('last_analytics_update', sa.DateTime(timezone=True), nullable=True))
    
    # Set default values for existing rows (PostgreSQL and SQLite compatible)
    op.execute("UPDATE content_items SET indexing_status = 'pending' WHERE indexing_status IS NULL")
    op.execute("UPDATE content_items SET impressions = 0 WHERE impressions IS NULL")
    op.execute("UPDATE content_items SET clicks = 0 WHERE clicks IS NULL")
    op.execute("UPDATE content_items SET engagement = 0 WHERE engagement IS NULL")
    op.execute("UPDATE content_items SET referrals = 0 WHERE referrals IS NULL")
    op.execute("UPDATE content_items SET conversions = 0 WHERE conversions IS NULL")


def downgrade():
    # Remove analytics columns
    op.drop_column('content_items', 'last_analytics_update')
    op.drop_column('content_items', 'conversions')
    op.drop_column('content_items', 'referrals')
    op.drop_column('content_items', 'engagement')
    op.drop_column('content_items', 'clicks')
    op.drop_column('content_items', 'impressions')
    
    # Remove SEO metadata columns
    op.drop_column('content_items', 'internal_links')
    op.drop_column('content_items', 'indexing_status')
    op.drop_column('content_items', 'canonical_url')
    op.drop_column('content_items', 'meta_description')
    op.drop_column('content_items', 'meta_title')
    op.drop_column('content_items', 'search_intent')
    op.drop_column('content_items', 'target_keyword')
    op.drop_column('content_items', 'source_urls')
    
    # Remove approval tracking columns
    op.drop_column('content_items', 'approver')
    op.drop_column('content_items', 'approved_at')
