import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.models.content_item import ContentItemModel
from apps.models.base import get_db
from apps.api.auth import create_test_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Create in-memory SQLite engine with proper connection pooling
async_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_test_db():
    """Test database dependency with proper session management."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@pytest_asyncio.fixture(autouse=True)
async def db_override():
    """Override database dependency for all tests."""
    app.dependency_overrides[get_db] = get_test_db
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_db():
    """Setup and teardown test database."""
    from apps.models.base import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Dispose engine to ensure all connections are closed
    await async_engine.dispose()

@pytest.mark.asyncio
async def test_edit_content_endpoint():
    async with AsyncSessionLocal() as session:
        item = ContentItemModel(id="edit-me", title="Old Title", channel="X", status="pending_review")
        session.add(item)
        await session.commit()

    token = create_test_token(role="operator")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch("/api/v1/content/edit-me", json={
            "title": "New Title",
            "body": "New Body"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["body"] == "New Body"
        assert data["status"] == "draft"

@pytest.mark.asyncio
async def test_list_content_queue_ordering():
    async with AsyncSessionLocal() as session:
        session.add(ContentItemModel(id="1", title="A", channel="X", status="approved"))
        session.add(ContentItemModel(id="2", title="B", channel="X", status="pending_review"))
        session.add(ContentItemModel(id="3", title="C", channel="X", status="draft"))
        await session.commit()

    token = create_test_token(role="viewer")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/content", headers=headers)
        assert response.status_code == 200
        items = response.json()
        
        statuses = [i["status"] for i in items]
        assert statuses[0] in ["pending_review", "draft"]
        assert statuses[1] in ["pending_review", "draft"]
        assert statuses[2] == "approved"
