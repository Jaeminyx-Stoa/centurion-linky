import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.user import User


@pytest_asyncio.fixture
async def cust_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="고객의원", slug="cust-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def cust_admin(db: AsyncSession, cust_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=cust_clinic.id,
        email="cust-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="고객관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def cust_token(client: AsyncClient, cust_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "cust-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def cust_headers(cust_token: str) -> dict:
    return {"Authorization": f"Bearer {cust_token}"}


@pytest_asyncio.fixture
async def customers(db: AsyncSession, cust_clinic: Clinic) -> list[Customer]:
    items = []
    for i in range(3):
        c = Customer(
            id=uuid.uuid4(),
            clinic_id=cust_clinic.id,
            messenger_type="telegram",
            messenger_user_id=f"tg_{i}",
            display_name=f"고객{i}",
            country_code=["JP", "CN", "US"][i],
            language_code=["ja", "zh", "en"][i],
        )
        db.add(c)
        items.append(c)
    await db.commit()
    for c in items:
        await db.refresh(c)
    return items


class TestListCustomers:
    async def test_list_customers(
        self, client: AsyncClient, cust_headers: dict, customers: list[Customer]
    ):
        resp = await client.get("/api/v1/customers", headers=cust_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_customers_empty(
        self, client: AsyncClient, cust_headers: dict
    ):
        resp = await client.get("/api/v1/customers", headers=cust_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_customers_only_own_clinic(
        self,
        client: AsyncClient,
        cust_headers: dict,
        customers: list[Customer],
        db: AsyncSession,
    ):
        """Customers from other clinics should not appear."""
        other_clinic = Clinic(
            id=uuid.uuid4(), name="타클리닉", slug="other-clinic"
        )
        db.add(other_clinic)
        other_customer = Customer(
            id=uuid.uuid4(),
            clinic_id=other_clinic.id,
            messenger_type="line",
            messenger_user_id="line_other",
            display_name="타고객",
        )
        db.add(other_customer)
        await db.commit()

        resp = await client.get("/api/v1/customers", headers=cust_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3  # only own clinic's customers
