import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def cu_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="고객의원", slug="cu-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def cu_admin(db: AsyncSession, cu_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=cu_clinic.id,
        email="cu-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="고객관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def cu_token(client: AsyncClient, cu_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "cu-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def cu_headers(cu_token: str) -> dict:
    return {"Authorization": f"Bearer {cu_token}"}


@pytest_asyncio.fixture
async def cu_customer(db: AsyncSession, cu_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=cu_clinic.id,
        messenger_type="telegram",
        messenger_user_id="cu-tg-user-1",
        name="테스트고객",
        country_code="KR",
        language_code="ko",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


# --- Tests ---
class TestListCustomers:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, cu_headers: dict, cu_customer: Customer
    ):
        resp = await client.get("/api/v1/customers", headers=cu_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_pagination(
        self, client: AsyncClient, cu_headers: dict, cu_customer: Customer
    ):
        resp = await client.get(
            "/api/v1/customers?limit=1&offset=0", headers=cu_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 1


class TestGetCustomer:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, cu_headers: dict, cu_customer: Customer
    ):
        resp = await client.get(
            f"/api/v1/customers/{cu_customer.id}", headers=cu_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(cu_customer.id)

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, cu_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/customers/{uuid.uuid4()}", headers=cu_headers
        )
        assert resp.status_code == 404


class TestUpdateCustomer:
    @pytest.mark.asyncio
    async def test_update_name(
        self, client: AsyncClient, cu_headers: dict, cu_customer: Customer
    ):
        resp = await client.patch(
            f"/api/v1/customers/{cu_customer.id}",
            json={"name": "새이름"},
            headers=cu_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "새이름"

    @pytest.mark.asyncio
    async def test_update_tags(
        self, client: AsyncClient, cu_headers: dict, cu_customer: Customer
    ):
        resp = await client.patch(
            f"/api/v1/customers/{cu_customer.id}",
            json={"tags": ["VIP", "returning"]},
            headers=cu_headers,
        )
        assert resp.status_code == 200
        assert "VIP" in resp.json()["tags"]
