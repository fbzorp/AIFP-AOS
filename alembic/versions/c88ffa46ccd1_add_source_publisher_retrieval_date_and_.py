"""add_source_publisher_retrieval_date_and_content_verification_fields

Revision ID: c88ffa46ccd1
Revises: 7ff8e3bbcdfd
Create Date: 2026-08-10 17:15:33.818328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c88ffa46ccd1'
down_revision = '7ff8e3bbcdfd'
branch_labels = None
depends_on = None


def upgrade():
    # Add publisher and retrieval_date columns to sources table
    op.add_column('sources', sa.Column('publisher', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('retrieval_date', sa.DateTime(timezone=True), nullable=True))
    
    # Add technical verification fields to content_items table
    op.add_column('content_items', sa.Column('technical_verification_status', sa.String(), nullable=True))
    op.add_column('content_items', sa.Column('technical_verification_details', sa.Text(), nullable=True))


def downgrade():
    # Remove technical verification fields from content_items table
    op.drop_column('content_items', 'technical_verification_details')
    op.drop_column('content_items', 'technical_verification_status')
    
    # Remove publisher and retrieval_date columns from sources table
    op.drop_column('sources', 'retrieval_date')
    op.drop_column('sources', 'publisher')
