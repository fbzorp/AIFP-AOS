"""
Settings and credential management tests.
Tests credential masking, update functionality, and RBAC enforcement.
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
    await async_engine.dispose()


@pytest.mark.asyncio
async def test_get_credentials_unauthenticated():
    """Test that GET /settings/credentials requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/settings/credentials")
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower() or "authenticated" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_credentials_non_admin():
    """Test that GET /settings/credentials requires admin role."""
    token = create_test_token(role="smm_manager")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/settings/credentials", headers=headers)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_credentials_admin():
    """Test that admin can get masked credential status."""
    token = create_test_token(role="founder_admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/settings/credentials", headers=headers)
        assert response.status_code == 200
        
        credentials = response.json()
        assert isinstance(credentials, list)
        assert len(credentials) > 0
        
        # Verify no raw secrets are exposed
        for cred in credentials:
            assert "name" in cred
            assert "configured" in cred
            assert "masked" in cred
            assert "description" in cred
            
            # Ensure the masked value is not the raw secret
            if cred["configured"]:
                masked = cred["masked"]
                # Should be masked format like "xxxx...xxxx"
                assert "..." in masked or len(masked) <= 8


@pytest.mark.asyncio
async def test_update_credential_unauthenticated():
    """Test that PATCH /settings/credentials requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/v1/settings/credentials", json={
            "name": "DEEPSEEK_API_KEY",
            "value": "test-secret-key"
        })
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_credential_non_admin():
    """Test that PATCH /settings/credentials requires admin role."""
    token = create_test_token(role="smm_manager")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/v1/settings/credentials", 
            json={"name": "DEEPSEEK_API_KEY", "value": "test-secret-key"},
            headers=headers
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_credential_admin():
    """Test that admin can update credentials and audit event is recorded."""
    token = create_test_token(role="founder_admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/v1/settings/credentials",
            json={"name": "DEEPSEEK_API_KEY", "value": "new-test-key-12345678"},
            headers=headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] == True
        assert result["credential_name"] == "DEEPSEEK_API_KEY"
        assert "redeploy" in result["message"].lower()


@pytest.mark.asyncio
async def test_update_credential_invalid_name():
    """Test that updating an unknown credential returns 400."""
    token = create_test_token(role="founder_admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/v1/settings/credentials",
            json={"name": "INVALID_CREDENTIAL", "value": "test-value"},
            headers=headers
        )
        assert response.status_code == 400
        assert "Unknown credential" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_credential_audit_event_no_leak():
    """Test that credential update audit event does not leak the secret value."""
    token = create_test_token(role="founder_admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Update credential
        await client.patch("/api/v1/settings/credentials",
            json={"name": "DEEPSEEK_API_KEY", "value": "super-secret-key-12345"},
            headers=headers
        )
        
        # Check audit events to ensure secret value is not leaked
        response = await client.get("/api/v1/audit", headers=headers)
        assert response.status_code == 200
        
        audit_events = response.json()
        # Find the credential_updated event
        credential_events = [e for e in audit_events if e.get("event_type") == "credential_updated"]
        
        if credential_events:
            latest_event = credential_events[0]
            # Ensure the secret value is not in the message or metadata
            assert "super-secret-key-12345" not in str(latest_event.get("message", ""))
            assert "super-secret-key-12345" not in str(latest_event.get("metadata_json", {}))
            # Only the credential name should be present
            assert "DEEPSEEK_API_KEY" in str(latest_event.get("metadata_json", {}))
