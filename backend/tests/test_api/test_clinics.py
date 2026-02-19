import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def clinic_data(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="마이클리닉",
        slug="my-clinic",
        phone="02-1234-5678",
        address="서울시 강남구",
        commission_rate=Decimal("15.00"),
        settings={"ai_mode": "auto", "language": "ko"},
    )
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def clinic_admin(db: AsyncSession, clinic_data: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=clinic_data.id,
        email="clinic-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="클리닉관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def clinic_token(client: AsyncClient, clinic_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "clinic-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def clinic_headers(clinic_token: str) -> dict:
    return {"Authorization": f"Bearer {clinic_token}"}


# --- GET /clinics/me ---
class TestGetClinicMe:
    async def test_get_clinic_me(
        self, client: AsyncClient, clinic_headers: dict, clinic_data: Clinic
    ):
        resp = await client.get("/api/v1/clinics/me", headers=clinic_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "마이클리닉"
        assert data["slug"] == "my-clinic"
        assert data["phone"] == "02-1234-5678"
        assert data["address"] == "서울시 강남구"
        assert float(data["commission_rate"]) == 15.0
        assert data["settings"]["ai_mode"] == "auto"

    async def test_get_clinic_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/clinics/me")
        assert resp.status_code == 401


# --- PATCH /clinics/me ---
class TestUpdateClinicMe:
    async def test_update_clinic_basic_info(
        self, client: AsyncClient, clinic_headers: dict, clinic_data: Clinic
    ):
        resp = await client.patch(
            "/api/v1/clinics/me",
            headers=clinic_headers,
            json={"name": "새이름클리닉", "phone": "02-9999-0000"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "새이름클리닉"
        assert data["phone"] == "02-9999-0000"
        # unchanged fields
        assert data["address"] == "서울시 강남구"

    async def test_update_clinic_address(
        self, client: AsyncClient, clinic_headers: dict, clinic_data: Clinic
    ):
        resp = await client.patch(
            "/api/v1/clinics/me",
            headers=clinic_headers,
            json={"address": "서울시 서초구 신반포로"},
        )
        assert resp.status_code == 200
        assert resp.json()["address"] == "서울시 서초구 신반포로"

    async def test_update_clinic_no_body(
        self, client: AsyncClient, clinic_headers: dict, clinic_data: Clinic
    ):
        resp = await client.patch(
            "/api/v1/clinics/me",
            headers=clinic_headers,
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "마이클리닉"


# --- PATCH /clinics/me/settings ---
class TestUpdateClinicSettings:
    async def test_update_settings(
        self, client: AsyncClient, clinic_headers: dict, clinic_data: Clinic
    ):
        resp = await client.patch(
            "/api/v1/clinics/me/settings",
            headers=clinic_headers,
            json={"settings": {"ai_mode": "manual", "new_key": "value"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Merged: original "language" key kept, "ai_mode" updated, "new_key" added
        assert data["settings"]["ai_mode"] == "manual"
        assert data["settings"]["new_key"] == "value"
        assert data["settings"]["language"] == "ko"

    async def test_update_settings_empty(
        self, client: AsyncClient, clinic_headers: dict, clinic_data: Clinic
    ):
        resp = await client.patch(
            "/api/v1/clinics/me/settings",
            headers=clinic_headers,
            json={"settings": {}},
        )
        assert resp.status_code == 200
        # Original settings unchanged
        assert resp.json()["settings"]["ai_mode"] == "auto"
