import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_body_within_limit(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "test"},
    )
    # Should not be 413 — may be 401 or other, but not blocked by body limit
    assert response.status_code != 413


async def test_body_exceeds_limit(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        content=b"x" * (11 * 1024 * 1024),  # 11MB > 10MB limit
        headers={"Content-Length": str(11 * 1024 * 1024), "Content-Type": "application/json"},
    )
    assert response.status_code == 413
