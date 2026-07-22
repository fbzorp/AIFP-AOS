# Enriched agents JSON columns migration

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'new_revision_id_placeholder'
down_revision = '4cc0d2d8f55e'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('agents', sa.Column('tools', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('inputs', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('outputs', sa.Column('outputs', sa.JSON(), nullable=True)))
    op.add_column('agents', sa.Column('policies', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('kpis', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('execution_history', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('agents', 'execution_history')
    op.drop_column('agents', 'kpis')
    op.drop_column('agents', 'policies')
    op.drop_column('agents', 'outputs')
    op.drop_column('agents', 'inputs')
    op.drop_column('agents', 'tools')