"""WebSocket endpoint tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Clinic, User
from app.websocket.manager import ConnectionManager


# --- Fixtures ---

@pytest.fixture
async def ws_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="WS테스트의원", slug="ws-test")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def ws_user(db: AsyncSession, ws_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=ws_clinic.id,
        email="admin@ws-test.com",
        password_hash=hash_password("password123"),
        name="WS관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def ws_token(ws_user: User) -> str:
    return create_access_token({"sub": str(ws_user.id)})


# --- ConnectionManager unit tests ---

class TestConnectionManager:
    def test_manager_creation(self):
        manager = ConnectionManager()
        assert manager is not None

    async def test_no_connections_initially(self):
        manager = ConnectionManager()
        count = manager.get_connection_count(uuid.uuid4())
        assert count == 0


# --- WebSocket auth tests ---

class TestWebSocketAuth:
    async def test_ws_rejects_no_token(self, client: AsyncClient):
        """WebSocket without token should be rejected."""
        from starlette.testclient import TestClient
        from app.main import app

        test_client = TestClient(app)
        with pytest.raises(Exception):
            with test_client.websocket_connect("/ws"):
                pass

    async def test_ws_rejects_invalid_token(self, client: AsyncClient):
        """WebSocket with invalid token should be rejected."""
        from starlette.testclient import TestClient
        from app.main import app

        test_client = TestClient(app)
        with pytest.raises(Exception):
            with test_client.websocket_connect("/ws?token=invalid"):
                pass

    async def test_ws_accepts_valid_token(self, ws_token: str):
        """WebSocket with valid token should connect."""
        from starlette.testclient import TestClient
        from app.main import app

        test_client = TestClient(app)
        with test_client.websocket_connect(f"/ws?token={ws_token}") as ws:
            # Should receive a connection confirmation
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert "clinic_id" in data


# --- Broadcast tests (unit) ---

class TestWebSocketBroadcast:
    async def test_broadcast_skips_when_no_connections(self):
        """Broadcasting to a clinic with no connections should not error."""
        mgr = ConnectionManager()
        await mgr.broadcast_to_clinic(
            uuid.uuid4(),
            {"type": "new_message", "conversation_id": str(uuid.uuid4())},
        )
        # No error means success
