import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.procedure import Procedure
from app.models.user import User


@pytest_asyncio.fixture
async def rev_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="매출의원", slug="revenue-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def rev_admin(db: AsyncSession, rev_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=rev_clinic.id,
        email="rev-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="매출관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def rev_token(client: AsyncClient, rev_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "rev-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def rev_headers(rev_token: str) -> dict:
    return {"Authorization": f"Bearer {rev_token}"}


@pytest_asyncio.fixture
async def rev_data(db: AsyncSession, rev_clinic: Clinic):
    """Create procedure, booking, and payment data for analytics tests."""
    proc = Procedure(
        id=uuid.uuid4(), name_ko="보톡스", name_en="Botox", slug="rev-botox"
    )
    db.add(proc)
    await db.flush()

    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=rev_clinic.id,
        procedure_id=proc.id,
        material_cost=Decimal("50000"),
    )
    db.add(cp)
    await db.flush()

    customer1 = Customer(
        id=uuid.uuid4(),
        clinic_id=rev_clinic.id,
        messenger_type="telegram",
        messenger_user_id="rev-cust-1",
        name="고객1",
        country_code="KR",
    )
    customer2 = Customer(
        id=uuid.uuid4(),
        clinic_id=rev_clinic.id,
        messenger_type="telegram",
        messenger_user_id="rev-cust-2",
        name="고객2",
        country_code="JP",
    )
    db.add(customer1)
    db.add(customer2)
    await db.flush()

    now = datetime.now(timezone.utc)
    for i, customer in enumerate([customer1, customer2]):
        booking = Booking(
            id=uuid.uuid4(),
            clinic_id=rev_clinic.id,
            customer_id=customer.id,
            clinic_procedure_id=cp.id,
            booking_date=date.today() - timedelta(days=i),
            booking_time=time(10 + i, 0),
            status="completed",
        )
        db.add(booking)
        await db.flush()

        payment = Payment(
            id=uuid.uuid4(),
            clinic_id=rev_clinic.id,
            booking_id=booking.id,
            customer_id=customer.id,
            payment_type="full",
            amount=Decimal("500000") if i == 0 else Decimal("300000"),
            currency="KRW",
            status="completed",
            paid_at=now - timedelta(hours=i * 2),
        )
        db.add(payment)

    await db.commit()
    return {"proc": proc, "cp": cp, "customers": [customer1, customer2]}


class TestProcedureProfitability:
    @pytest.mark.asyncio
    async def test_returns_procedure_data(
        self, client: AsyncClient, rev_headers: dict, rev_data
    ):
        resp = await client.get(
            "/api/v1/analytics/procedure-profitability?days=30",
            headers=rev_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "procedures" in data
        assert len(data["procedures"]) >= 1

        proc = data["procedures"][0]
        assert "procedure_name" in proc
        assert "case_count" in proc
        assert "total_revenue" in proc
        assert "margin_rate" in proc
        assert proc["total_revenue"] > 0

    @pytest.mark.asyncio
    async def test_empty_data(self, client: AsyncClient, rev_headers: dict):
        resp = await client.get(
            "/api/v1/analytics/procedure-profitability?days=1",
            headers=rev_headers,
        )
        assert resp.status_code == 200


class TestCustomerLifetimeValue:
    @pytest.mark.asyncio
    async def test_returns_customer_data(
        self, client: AsyncClient, rev_headers: dict, rev_data
    ):
        resp = await client.get(
            "/api/v1/analytics/customer-lifetime-value?days=365&top_n=10",
            headers=rev_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "customers" in data
        assert "nationality_avg" in data
        assert len(data["customers"]) >= 1

        customer = data["customers"][0]
        assert "customer_name" in customer
        assert "total_payments" in customer
        assert "predicted_annual_value" in customer

    @pytest.mark.asyncio
    async def test_nationality_avg_populated(
        self, client: AsyncClient, rev_headers: dict, rev_data
    ):
        resp = await client.get(
            "/api/v1/analytics/customer-lifetime-value?days=365",
            headers=rev_headers,
        )
        data = resp.json()
        assert len(data["nationality_avg"]) >= 1
        nat = data["nationality_avg"][0]
        assert "country_code" in nat
        assert "avg_clv" in nat


class TestRevenueHeatmap:
    @pytest.mark.asyncio
    async def test_returns_heatmap(
        self, client: AsyncClient, rev_headers: dict, rev_data
    ):
        resp = await client.get(
            "/api/v1/analytics/revenue-heatmap?days=30",
            headers=rev_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "heatmap" in data
        assert "peak_slots" in data
        assert isinstance(data["heatmap"], list)

        if len(data["heatmap"]) > 0:
            cell = data["heatmap"][0]
            assert "day_of_week" in cell
            assert "hour" in cell
            assert "count" in cell
            assert "total_amount" in cell

    @pytest.mark.asyncio
    async def test_empty_heatmap(self, client: AsyncClient, rev_headers: dict):
        resp = await client.get(
            "/api/v1/analytics/revenue-heatmap?days=1",
            headers=rev_headers,
        )
        assert resp.status_code == 200
