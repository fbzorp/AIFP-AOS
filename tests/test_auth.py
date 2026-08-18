"""
Authentication and authorization tests.
Tests JWT-based authentication and RBAC enforcement on protected endpoints.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.auth import create_test_token
from apps.models.base import get_db
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
async def test_authenticated_content_approval():
    """Test that content approval succeeds with approve permission."""
    token = create_test_token(role="smm_manager")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/content/test_id/approve", json={
            "approved_by": "test_user",
            "expires_in_hours": 24
        }, headers=headers)
        # Should fail with 404 (content not found) but auth check passed
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_smm_manager_can_approve_and_publish():
    """Test that smm_manager role can approve and publish content."""
    token = create_test_token(role="smm_manager")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test approve endpoint
        response = await client.post("/api/v1/content/test_id/approve", json={
            "approved_by": "test_user",
            "expires_in_hours": 24
        }, headers=headers)
        # Should fail with 404 (content not found) but auth check passed
        assert response.status_code == 404
        
        # Test publish endpoint
        response = await client.post("/api/v1/content/test_id/publish", headers=headers)
        # Should fail with 404 (content not found) but auth check passed
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_viewer_cannot_approve_or_publish():
    """Test that viewer role is rejected on approve/publish endpoints."""
    token = create_test_token(role="viewer")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test approve endpoint
        response = await client.post("/api/v1/content/test_id/approve", json={
            "approved_by": "test_user",
            "expires_in_hours": 24
        }, headers=headers)
        # Should fail with 403 (insufficient permissions)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        
        # Test publish endpoint
        response = await client.post("/api/v1/content/test_id/publish", headers=headers)
        # Should fail with 403 (insufficient permissions)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_service_agent_cannot_approve_or_publish():
    """Test that service_agent role is rejected on approve/publish endpoints."""
    token = create_test_token(role="service_agent")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test approve endpoint
        response = await client.post("/api/v1/content/test_id/approve", json={
            "approved_by": "test_user",
            "expires_in_hours": 24
        }, headers=headers)
        # Should fail with 403 (insufficient permissions)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        
        # Test publish endpoint
        response = await client.post("/api/v1/content/test_id/publish", headers=headers)
        # Should fail with 403 (insufficient permissions)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_missing_authorization_header():
    """Test that missing Authorization header returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/content/test_id/approve", json={
            "approved_by": "test_user",
            "expires_in_hours": 24
        })
        # Should fail with 401 (unauthenticated)
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower() or "authenticated" in response.json()["detail"].lower()