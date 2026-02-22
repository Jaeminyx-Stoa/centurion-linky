"""Tests for platform admin API endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.clinic import Clinic
from app.models.user import User


@pytest.fixture
async def superadmin_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="관리자클리닉", slug="admin-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def superadmin(db: AsyncSession, superadmin_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=superadmin_clinic.id,
        email="superadmin@test.com",
        password_hash=hash_password("password123"),
        name="슈퍼관리자",
        role="superadmin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def regular_user(db: AsyncSession, superadmin_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=superadmin_clinic.id,
        email="staff@test.com",
        password_hash=hash_password("password123"),
        name="일반직원",
        role="staff",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def superadmin_token(superadmin: User) -> str:
    return create_access_token(str(superadmin.id))


@pytest.fixture
def regular_token(regular_user: User) -> str:
    return create_access_token(str(regular_user.id))


@pytest.fixture
async def clinics(db: AsyncSession) -> list[Clinic]:
    clinics = [
        Clinic(id=uuid.uuid4(), name="클리닉A", slug="clinic-a"),
        Clinic(id=uuid.uuid4(), name="클리닉B", slug="clinic-b"),
    ]
    for c in clinics:
        db.add(c)
    await db.commit()
    return clinics


class TestAdminListClinics:
    @pytest.mark.asyncio
    async def test_superadmin_can_list(
        self, client: AsyncClient, superadmin_token: str, clinics
    ):
        resp = await client.get(
            "/api/v1/admin/clinics",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        # At least the superadmin's clinic + 2 test clinics
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_non_superadmin_forbidden(
        self, client: AsyncClient, regular_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/clinics",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert resp.status_code == 403


class TestAdminGetClinic:
    @pytest.mark.asyncio
    async def test_get_clinic(
        self, client: AsyncClient, superadmin_token: str, clinics
    ):
        resp = await client.get(
            f"/api/v1/admin/clinics/{clinics[0].id}",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "클리닉A"

    @pytest.mark.asyncio
    async def test_get_nonexistent_clinic(
        self, client: AsyncClient, superadmin_token: str
    ):
        resp = await client.get(
            f"/api/v1/admin/clinics/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 404


class TestAdminUpdateClinic:
    @pytest.mark.asyncio
    async def test_update_commission_rate(
        self, client: AsyncClient, superadmin_token: str, clinics
    ):
        resp = await client.patch(
            f"/api/v1/admin/clinics/{clinics[0].id}",
            json={"commission_rate": 15.5},
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["commission_rate"] == 15.5

    @pytest.mark.asyncio
    async def test_deactivate_clinic(
        self, client: AsyncClient, superadmin_token: str, clinics
    ):
        resp = await client.patch(
            f"/api/v1/admin/clinics/{clinics[0].id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


class TestPlatformAnalytics:
    @pytest.mark.asyncio
    async def test_analytics(
        self, client: AsyncClient, superadmin_token: str, clinics
    ):
        resp = await client.get(
            "/api/v1/admin/analytics/platform",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_clinics" in data
        assert "active_clinics" in data
        assert "total_conversations" in data
        assert data["total_clinics"] >= 3  # superadmin's + 2 test clinics
