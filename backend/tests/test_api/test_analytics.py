import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.consultation_performance import ConsultationPerformance
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.models.user import User


@pytest_asyncio.fixture
async def an_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="분석의원", slug="analytics-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def an_admin(db: AsyncSession, an_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=an_clinic.id,
        email="an-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="분석관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def an_token(client: AsyncClient, an_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "an-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def an_headers(an_token: str) -> dict:
    return {"Authorization": f"Bearer {an_token}"}


@pytest_asyncio.fixture
async def an_data(db: AsyncSession, an_clinic: Clinic):
    """Create conversations, bookings, payments for analytics."""
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=an_clinic.id,
        messenger_type="telegram",
        account_name="analytics_bot",
        credentials={"bot_token": "test"},
        is_active=True,
    )
    db.add(account)

    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=an_clinic.id,
        messenger_type="telegram",
        messenger_user_id="tg_an_1",
        display_name="분석고객",
    )
    db.add(customer)
    await db.flush()

    # 5 conversations (3 active, 2 resolved)
    convs = []
    for i in range(5):
        conv = Conversation(
            id=uuid.uuid4(),
            clinic_id=an_clinic.id,
            customer_id=customer.id,
            messenger_account_id=account.id,
            status="resolved" if i < 2 else "active",
            created_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
        )
        db.add(conv)
        convs.append(conv)

    # 3 bookings
    for i in range(3):
        booking = Booking(
            id=uuid.uuid4(),
            clinic_id=an_clinic.id,
            customer_id=customer.id,
            conversation_id=convs[i].id,
            status="confirmed",
            booking_date=datetime(2026, 1, 15).date(),
            booking_time=datetime(2026, 1, 15, 10, 0).time(),
            created_at=datetime(2026, 1, 12, tzinfo=timezone.utc),
        )
        db.add(booking)

    # 2 payments
    for i in range(2):
        payment = Payment(
            id=uuid.uuid4(),
            clinic_id=an_clinic.id,
            customer_id=customer.id,
            booking_id=None,
            payment_type="deposit",
            amount=Decimal("100000"),
            currency="KRW",
            status="completed",
            pg_provider="stub",
            created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        db.add(payment)

    # Performance record
    perf = ConsultationPerformance(
        id=uuid.uuid4(),
        clinic_id=an_clinic.id,
        period_year=2026,
        period_month=1,
        total_score=Decimal("75.50"),
        sales_mix_score=Decimal("30.00"),
        booking_conversion_score=Decimal("25.00"),
        payment_conversion_score=Decimal("20.50"),
        booking_conversion_rate=Decimal("60.00"),
        payment_conversion_rate=Decimal("66.67"),
        total_consultations=5,
        total_bookings=3,
        total_payments=2,
    )
    db.add(perf)

    await db.commit()


class TestAnalyticsOverview:
    async def test_overview(
        self, client: AsyncClient, an_headers: dict, an_data
    ):
        resp = await client.get(
            "/api/v1/analytics/overview", headers=an_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_conversations"] == 5
        assert data["active_conversations"] == 3
        assert data["resolved_conversations"] == 2
        assert data["total_bookings"] == 3
        assert data["total_payments"] == 2

    async def test_overview_empty(
        self, client: AsyncClient, an_headers: dict
    ):
        resp = await client.get(
            "/api/v1/analytics/overview", headers=an_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_conversations"] == 0


class TestConsultationPerformanceAPI:
    async def test_get_performance(
        self, client: AsyncClient, an_headers: dict, an_data
    ):
        resp = await client.get(
            "/api/v1/analytics/consultation-performance?year=2026&month=1",
            headers=an_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_score"]) == 75.5
        assert float(data["sales_mix_score"]) == 30.0
        assert data["total_consultations"] == 5
        assert data["total_bookings"] == 3

    async def test_get_performance_not_found(
        self, client: AsyncClient, an_headers: dict
    ):
        resp = await client.get(
            "/api/v1/analytics/consultation-performance?year=2026&month=1",
            headers=an_headers,
        )
        assert resp.status_code == 404
