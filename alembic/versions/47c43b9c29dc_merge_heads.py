"""merge_heads

Revision ID: 47c43b9c29dc
Revises: f3a8b2c1d4e5, c88ffa46ccd1
Create Date: 2026-08-10 18:48:23.856169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47c43b9c29dc'
down_revision = ('f3a8b2c1d4e5', 'c88ffa46ccd1')
branch_labels = None
depends_on = None


def upgrade():
    # Drop the obsolete credentials table (from the old credential system)
    try:
        op.drop_table('credentials')
    except Exception:
        # Table may not exist, ignore error
        pass
    
    # Drop credentials indexes if they exist
    try:
        op.drop_index('ix_credentials_agent_name', table_name='credentials')
        op.drop_index('ix_credentials_platform', table_name='credentials')
        op.drop_index('idx_agent_platform', table_name='credentials')
    except Exception:
        # Indexes may not exist, ignore error
        pass


def downgrade():
    # Recreate credentials table for rollback
    op.create_table('credentials',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('agent_name', sa.String(), nullable=False),
    sa.Column('platform', sa.String(), nullable=False),
    sa.Column('x_api_key', sa.String(), nullable=True),
    sa.Column('x_api_secret', sa.String(), nullable=True),
    sa.Column('x_access_token', sa.String(), nullable=True),
    sa.Column('x_access_token_secret', sa.String(), nullable=True),
    sa.Column('moltbook_agent_api_key', sa.String(), nullable=True),
    sa.Column('moltbook_app_key', sa.String(), nullable=True),
    sa.Column('telegram_bot_token', sa.String(), nullable=True),
    sa.Column('telegram_chat_id', sa.String(), nullable=True),
    sa.Column('telegram_default_channel', sa.String(), nullable=True),
    sa.Column('x_autopublish', sa.Boolean(), nullable=True),
    sa.Column('moltbook_autopublish', sa.Boolean(), nullable=True),
    sa.Column('telegram_autopublish', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agent_platform', 'credentials', ['agent_name', 'platform'], unique=False)
    op.create_index('ix_credentials_agent_name', 'credentials', ['agent_name'], unique=False)
    op.create_index('ix_credentials_platform', 'credentials', ['platform'], unique=False)
