import contextlib
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from apps.api.config import settings

Base = declarative_base()

# Async Engine & Session (for FastAPI)
async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync Engine & Session (for Dramatiq Workers)
# Convert asyncpg URL to psycopg2 URL
sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_db_url)
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    """FastAPI dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@contextlib.contextmanager
def get_sync_session():
    """Context manager for synchronous database sessions in workers."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_engine(database_url: str):
    """Legacy helper for backward compatibility."""
    return create_engine(database_url.replace("+asyncpg", "+psycopg2"))

def get_sessionmaker(database_url: str):
    """Legacy helper for backward compatibility."""
    engine = get_engine(database_url)
    return sessionmaker(bind=engine)
