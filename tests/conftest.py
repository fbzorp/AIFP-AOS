"""
Test configuration and fixtures.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from apps.models.base import Base
from apps.api.main import app
from apps.api.config import settings


@pytest.fixture
async def async_client():
    """Async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db():
    """Async database session for testing."""
    engine = create_async_engine(settings.DATABASE_URL.replace("+asyncpg", ""), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session