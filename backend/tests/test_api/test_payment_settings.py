import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def ps_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="결제설정의원",
        slug="ps-clinic",
        settings={"payment": {"default_currency": "KRW"}},
    )
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def ps_admin(db: AsyncSession, ps_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=ps_clinic.id,
        email="ps-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="결제관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def ps_token(client: AsyncClient, ps_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ps-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def ps_headers(ps_token: str) -> dict:
    return {"Authorization": f"Bearer {ps_token}"}


# --- Tests ---
class TestGetPaymentSettings:
    @pytest.mark.asyncio
    async def test_get_settings(
        self, client: AsyncClient, ps_headers: dict
    ):
        resp = await client.get("/api/v1/payment-settings", headers=ps_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_currency"] == "KRW"


class TestUpdatePaymentSettings:
    @pytest.mark.asyncio
    async def test_update_currency(
        self, client: AsyncClient, ps_headers: dict
    ):
        resp = await client.patch(
            "/api/v1/payment-settings",
            json={"default_currency": "USD"},
            headers=ps_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_currency"] == "USD"

    @pytest.mark.asyncio
    async def test_update_preserves_existing(
        self, client: AsyncClient, ps_headers: dict
    ):
        # First set some settings
        await client.patch(
            "/api/v1/payment-settings",
            json={"default_currency": "JPY"},
            headers=ps_headers,
        )
        # Verify preserved
        resp = await client.get("/api/v1/payment-settings", headers=ps_headers)
        assert resp.status_code == 200
        assert resp.json()["default_currency"] == "JPY"
