import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.services.performance_service import PerformanceService, rate_to_score


# --- rate_to_score tests ---
class TestRateToScore:
    def test_high_rate(self):
        thresholds = [(90, 30), (80, 25), (70, 20)]
        assert rate_to_score(95, thresholds) == 30

    def test_mid_rate(self):
        thresholds = [(90, 30), (80, 25), (70, 20)]
        assert rate_to_score(85, thresholds) == 25

    def test_low_rate(self):
        thresholds = [(90, 30), (80, 25), (70, 20)]
        assert rate_to_score(60, thresholds) == 5.0  # default

    def test_exact_threshold(self):
        thresholds = [(90, 30), (80, 25), (70, 20)]
        assert rate_to_score(80, thresholds) == 25


# --- Fixtures ---
@pytest_asyncio.fixture
async def perf_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="퍼포먼스의원", slug="perf-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def perf_customer(db: AsyncSession, perf_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=perf_clinic.id,
        messenger_type="telegram",
        messenger_user_id="perf-tg-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def perf_account(db: AsyncSession, perf_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=perf_clinic.id,
        messenger_type="telegram",
        account_name="perf-bot",
        credentials={"token": "test"},
        is_active=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def perf_data(
    db: AsyncSession,
    perf_clinic: Clinic,
    perf_customer: Customer,
    perf_account: MessengerAccount,
) -> dict:
    """Create 10 conversations, 8 bookings, 6 completed payments in Jan 2026."""
    jan = datetime(2026, 1, 15, tzinfo=timezone.utc)

    convs = []
    for i in range(10):
        conv = Conversation(
            id=uuid.uuid4(),
            clinic_id=perf_clinic.id,
            customer_id=perf_customer.id,
            messenger_account_id=perf_account.id,
            status="active",
            created_at=jan,
        )
        db.add(conv)
        convs.append(conv)

    bookings = []
    for i in range(8):
        bk = Booking(
            id=uuid.uuid4(),
            clinic_id=perf_clinic.id,
            customer_id=perf_customer.id,
            booking_date=date(2026, 1, 10 + i),
            booking_time=time(14, 0),
            status="confirmed",
            total_amount=Decimal("100000"),
            created_at=jan,
        )
        db.add(bk)
        bookings.append(bk)

    for i in range(6):
        pay = Payment(
            id=uuid.uuid4(),
            clinic_id=perf_clinic.id,
            customer_id=perf_customer.id,
            payment_type="full",
            amount=Decimal("100000"),
            currency="KRW",
            status="completed",
            paid_at=datetime(2026, 1, 15 + i, tzinfo=timezone.utc),
        )
        db.add(pay)

    await db.commit()
    return {"conversations": len(convs), "bookings": len(bookings), "payments": 6}


# --- Tests ---
class TestCalculatePerformance:
    @pytest.mark.asyncio
    async def test_basic_calculation(
        self, db: AsyncSession, perf_clinic: Clinic, perf_data: dict
    ):
        service = PerformanceService(db)
        perf = await service.calculate_performance(perf_clinic.id, 2026, 1)
        assert perf is not None
        assert perf.clinic_id == perf_clinic.id
        assert perf.period_year == 2026
        assert perf.period_month == 1

    @pytest.mark.asyncio
    async def test_counts(
        self, db: AsyncSession, perf_clinic: Clinic, perf_data: dict
    ):
        service = PerformanceService(db)
        perf = await service.calculate_performance(perf_clinic.id, 2026, 1)
        assert perf.total_consultations == 10
        assert perf.total_bookings == 8
        assert perf.total_payments == 6

    @pytest.mark.asyncio
    async def test_conversion_rates(
        self, db: AsyncSession, perf_clinic: Clinic, perf_data: dict
    ):
        service = PerformanceService(db)
        perf = await service.calculate_performance(perf_clinic.id, 2026, 1)
        # 8/10 = 80%
        assert perf.booking_conversion_rate == Decimal("80.00")
        # 6/8 = 75%
        assert perf.payment_conversion_rate == Decimal("75.00")

    @pytest.mark.asyncio
    async def test_scores(
        self, db: AsyncSession, perf_clinic: Clinic, perf_data: dict
    ):
        service = PerformanceService(db)
        perf = await service.calculate_performance(perf_clinic.id, 2026, 1)
        # booking rate 80% → score 25
        assert perf.booking_conversion_score == Decimal("25")
        # payment rate 75% → score 10
        assert perf.payment_conversion_score == Decimal("10")
        assert perf.total_score > 0

    @pytest.mark.asyncio
    async def test_idempotent(
        self, db: AsyncSession, perf_clinic: Clinic, perf_data: dict
    ):
        service = PerformanceService(db)
        p1 = await service.calculate_performance(perf_clinic.id, 2026, 1)
        await db.flush()
        p2 = await service.calculate_performance(perf_clinic.id, 2026, 1)
        assert p1.id == p2.id

    @pytest.mark.asyncio
    async def test_empty_period(self, db: AsyncSession, perf_clinic: Clinic):
        service = PerformanceService(db)
        perf = await service.calculate_performance(perf_clinic.id, 2026, 6)
        assert perf.total_consultations == 0
        assert perf.total_bookings == 0
        assert perf.total_payments == 0
        assert perf.booking_conversion_rate == Decimal("0.00")
