import pytest
import httpx


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert "version" in data


def test_root_endpoint():
    r = httpx.get("http://localhost:8000/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
