import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_request_id_in_response_header(client: AsyncClient):
    response = await client.get("/health")
    assert "X-Request-ID" in response.headers
    # UUID format check
    req_id = response.headers["X-Request-ID"]
    assert len(req_id) == 36
    assert req_id.count("-") == 4
