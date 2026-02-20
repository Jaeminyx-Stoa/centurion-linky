import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.clinic import Clinic
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def au_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="감사의원", slug="au-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def au_admin(db: AsyncSession, au_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=au_clinic.id,
        email="au-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="감사관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def au_token(client: AsyncClient, au_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "au-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def au_headers(au_token: str) -> dict:
    return {"Authorization": f"Bearer {au_token}"}


@pytest_asyncio.fixture
async def au_log_entries(db: AsyncSession, au_clinic: Clinic, au_admin: User) -> list[AuditLog]:
    entries = []
    for action in ("login", "toggle_ai", "cancel_event"):
        log = AuditLog(
            id=uuid.uuid4(),
            clinic_id=au_clinic.id,
            user_id=au_admin.id,
            action=action,
            resource_type="test",
            resource_id=str(uuid.uuid4()),
        )
        db.add(log)
        entries.append(log)
    await db.commit()
    return entries


# --- Tests ---
class TestListAuditLogs:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, au_headers: dict, au_log_entries: list[AuditLog]
    ):
        resp = await client.get("/api/v1/audit-logs", headers=au_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_filter_by_action(
        self, client: AsyncClient, au_headers: dict, au_log_entries: list[AuditLog]
    ):
        resp = await client.get(
            "/api/v1/audit-logs?action=login", headers=au_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["action"] == "login" for item in data["items"])

    @pytest.mark.asyncio
    async def test_filter_by_resource_type(
        self, client: AsyncClient, au_headers: dict, au_log_entries: list[AuditLog]
    ):
        resp = await client.get(
            "/api/v1/audit-logs?resource_type=test", headers=au_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_pagination(
        self, client: AsyncClient, au_headers: dict, au_log_entries: list[AuditLog]
    ):
        resp = await client.get(
            "/api/v1/audit-logs?limit=1&offset=0", headers=au_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 1
        assert len(data["items"]) == 1

    @pytest.mark.asyncio
    async def test_empty_result(
        self, client: AsyncClient, au_headers: dict, au_log_entries: list[AuditLog]
    ):
        resp = await client.get(
            "/api/v1/audit-logs?action=nonexistent", headers=au_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
