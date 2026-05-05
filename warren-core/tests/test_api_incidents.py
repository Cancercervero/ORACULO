# warren-core/tests/test_api_incidents.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.dependencies import get_db, get_redis


@pytest_asyncio.fixture
async def client():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.sadd.return_value = 1
    mock_redis.srem.return_value = 1
    mock_redis.delete.return_value = 1

    mock_db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = execute_result

    async def override_get_db():
        yield mock_db

    def override_get_redis():
        return mock_redis

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_incidents_returns_empty(client):
    resp = await client.get("/incidents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_incident_unknown_template(client):
    resp = await client.post("/incidents", json={"title": "Test", "region": "Baltic", "template": "bogus"})
    assert resp.status_code == 400
