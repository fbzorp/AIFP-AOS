"""
Test configuration and fixtures.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app


@pytest.fixture
async def async_client():
    """Async HTTP client for testing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client