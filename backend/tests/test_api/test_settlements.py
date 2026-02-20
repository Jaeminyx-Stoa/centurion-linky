import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def stl_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="정산API의원",
        slug="stl-api-clinic",
        commission_rate=Decimal("10.00"),
    )
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def stl_admin(db: AsyncSession, stl_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=stl_clinic.id,
        email="stl-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="정산관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def stl_token(client: AsyncClient, stl_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "stl-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def stl_headers(stl_token: str) -> dict:
    return {"Authorization": f"Bearer {stl_token}"}


@pytest_asyncio.fixture
async def stl_payments(db: AsyncSession, stl_clinic: Clinic) -> list[Payment]:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=stl_clinic.id,
        messenger_type="telegram",
        messenger_user_id="stl-api-tg-1",
    )
    db.add(customer)
    payments = []
    for i in range(2):
        p = Payment(
            id=uuid.uuid4(),
            clinic_id=stl_clinic.id,
            customer_id=customer.id,
            payment_type="full",
            amount=Decimal("150000.00"),
            currency="KRW",
            status="completed",
            paid_at=datetime(2026, 1, 10 + i, tzinfo=timezone.utc),
        )
        db.add(p)
        payments.append(p)
    await db.commit()
    for p in payments:
        await db.refresh(p)
    return payments


# --- Tests ---
class TestGenerateSettlement:
    @pytest.mark.asyncio
    async def test_generate(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        resp = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["period_year"] == 2026
        assert data["period_month"] == 1
        assert data["status"] == "pending"
        assert float(data["total_payment_amount"]) == 300000.00
        assert data["total_payment_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_idempotent(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        resp1 = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        resp2 = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        assert resp1.json()["id"] == resp2.json()["id"]


class TestListSettlements:
    @pytest.mark.asyncio
    async def test_list_empty(
        self, client: AsyncClient, stl_headers: dict
    ):
        resp = await client.get(
            "/api/v1/settlements", headers=stl_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_with_filter(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        # Generate settlement first
        await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        resp = await client.get(
            "/api/v1/settlements?year=2026&month=1", headers=stl_headers
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_list_year_filter_no_match(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        resp = await client.get(
            "/api/v1/settlements?year=2025", headers=stl_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestGetSettlement:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        create_resp = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        sid = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/settlements/{sid}", headers=stl_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, stl_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/settlements/{uuid.uuid4()}", headers=stl_headers
        )
        assert resp.status_code == 404


class TestConfirmSettlement:
    @pytest.mark.asyncio
    async def test_confirm_pending(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        create_resp = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        sid = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/settlements/{sid}/confirm", headers=stl_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"
        assert resp.json()["confirmed_at"] is not None

    @pytest.mark.asyncio
    async def test_confirm_already_confirmed(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        create_resp = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        sid = create_resp.json()["id"]
        await client.patch(
            f"/api/v1/settlements/{sid}/confirm", headers=stl_headers
        )
        # Try to confirm again
        resp = await client.patch(
            f"/api/v1/settlements/{sid}/confirm", headers=stl_headers
        )
        assert resp.status_code == 400


class TestMarkPaid:
    @pytest.mark.asyncio
    async def test_mark_paid_confirmed(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        create_resp = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        sid = create_resp.json()["id"]
        # Confirm first
        await client.patch(
            f"/api/v1/settlements/{sid}/confirm", headers=stl_headers
        )
        # Mark paid
        resp = await client.patch(
            f"/api/v1/settlements/{sid}/mark-paid", headers=stl_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "paid"
        assert resp.json()["paid_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_paid_pending_fails(
        self, client: AsyncClient, stl_headers: dict, stl_payments: list[Payment]
    ):
        create_resp = await client.post(
            "/api/v1/settlements/generate",
            json={"year": 2026, "month": 1},
            headers=stl_headers,
        )
        sid = create_resp.json()["id"]
        # Try to mark paid without confirming
        resp = await client.patch(
            f"/api/v1/settlements/{sid}/mark-paid", headers=stl_headers
        )
        assert resp.status_code == 400
