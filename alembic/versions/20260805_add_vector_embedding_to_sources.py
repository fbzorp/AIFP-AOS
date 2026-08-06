"""add_vector_embedding_to_sources

Revision ID: f3a8b2c1d4e5
Revises: 20260729_add_payments
Create Date: 2026-08-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'f3a8b2c1d4e5'
down_revision = '20260729_add_payments'
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Add embedding column to sources table using pgvector Vector type
    # Use IF NOT EXISTS to avoid conflicts
    try:
        op.add_column('sources', sa.Column('embedding', Vector(384), nullable=True))
    except Exception:
        # Column might already exist, continue
        pass
    
    # Create HNSW index for cosine distance (guarded in case HNSW is not available)
    try:
        op.execute("""
            CREATE INDEX IF NOT EXISTS ix_sources_embedding_hnsw 
            ON sources USING hnsw (embedding vector_cosine_ops)
        """)
    except Exception:
        # Fallback to IVFFlat if HNSW is not available
        try:
            op.execute("""
                CREATE INDEX IF NOT EXISTS ix_sources_embedding_ivfflat 
                ON sources USING ivfflat (embedding vector_cosine_ops)
            """)
        except Exception:
            # If both fail, continue without index (degrades gracefully)
            pass


def downgrade():
    # Drop index if it exists
    try:
        op.execute("DROP INDEX IF EXISTS ix_sources_embedding_hnsw")
    except Exception:
        pass
    try:
        op.execute("DROP INDEX IF EXISTS ix_sources_embedding_ivfflat")
    except Exception:
        pass
    
    # Drop embedding column
    op.drop_column('sources', 'embedding')
    
    # Note: We don't drop the vector extension as it might be used elsewhere
    # To fully clean up, you would need: op.execute("DROP EXTENSION IF EXISTS vector")
