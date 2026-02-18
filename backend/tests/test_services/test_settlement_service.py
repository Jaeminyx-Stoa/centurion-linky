import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.services.settlement_service import SettlementService


# --- Fixtures ---
@pytest_asyncio.fixture
async def stl_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="정산의원",
        slug="stl-clinic",
        commission_rate=Decimal("10.00"),
    )
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def stl_clinic_b(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="정산의원B",
        slug="stl-clinic-b",
        commission_rate=Decimal("15.00"),
    )
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def stl_customer(db: AsyncSession, stl_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=stl_clinic.id,
        messenger_type="telegram",
        messenger_user_id="stl-tg-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def stl_payments(
    db: AsyncSession, stl_clinic: Clinic, stl_customer: Customer
) -> list[Payment]:
    """Create 3 completed payments in Jan 2026."""
    payments = []
    for i in range(3):
        p = Payment(
            id=uuid.uuid4(),
            clinic_id=stl_clinic.id,
            customer_id=stl_customer.id,
            payment_type="full",
            amount=Decimal("100000.00"),
            currency="KRW",
            status="completed",
            paid_at=datetime(2026, 1, 15 + i, tzinfo=timezone.utc),
        )
        db.add(p)
        payments.append(p)
    # Also add a pending payment (should NOT be included)
    pending = Payment(
        id=uuid.uuid4(),
        clinic_id=stl_clinic.id,
        customer_id=stl_customer.id,
        payment_type="deposit",
        amount=Decimal("50000.00"),
        currency="KRW",
        status="pending",
    )
    db.add(pending)
    await db.commit()
    for p in payments:
        await db.refresh(p)
    return payments


# --- Tests ---
class TestGenerateMonthlySettlement:
    @pytest.mark.asyncio
    async def test_basic_settlement(
        self, db: AsyncSession, stl_clinic: Clinic, stl_payments: list[Payment]
    ):
        service = SettlementService(db)
        settlement = await service.generate_monthly_settlement(
            stl_clinic.id, 2026, 1
        )
        assert settlement is not None
        assert settlement.clinic_id == stl_clinic.id
        assert settlement.period_year == 2026
        assert settlement.period_month == 1
        assert settlement.status == "pending"

    @pytest.mark.asyncio
    async def test_correct_amounts(
        self, db: AsyncSession, stl_clinic: Clinic, stl_payments: list[Payment]
    ):
        service = SettlementService(db)
        settlement = await service.generate_monthly_settlement(
            stl_clinic.id, 2026, 1
        )
        # 3 payments x 100,000 = 300,000
        assert settlement.total_payment_amount == Decimal("300000.00")
        assert settlement.total_payment_count == 3
        # commission 10% of 300,000 = 30,000
        assert settlement.commission_rate == Decimal("10.00")
        assert settlement.commission_amount == Decimal("30000.00")
        # VAT 10% of commission = 3,000
        assert settlement.vat_amount == Decimal("3000.00")
        # Total settlement = commission + VAT = 33,000
        assert settlement.total_settlement == Decimal("33000.00")

    @pytest.mark.asyncio
    async def test_excludes_pending_payments(
        self, db: AsyncSession, stl_clinic: Clinic, stl_payments: list[Payment]
    ):
        service = SettlementService(db)
        settlement = await service.generate_monthly_settlement(
            stl_clinic.id, 2026, 1
        )
        # Only 3 completed, not the pending one
        assert settlement.total_payment_count == 3

    @pytest.mark.asyncio
    async def test_no_payments_returns_zero_settlement(
        self, db: AsyncSession, stl_clinic: Clinic
    ):
        service = SettlementService(db)
        settlement = await service.generate_monthly_settlement(
            stl_clinic.id, 2026, 3
        )
        assert settlement.total_payment_amount == Decimal("0.00")
        assert settlement.total_payment_count == 0
        assert settlement.commission_amount == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_idempotent_returns_existing(
        self, db: AsyncSession, stl_clinic: Clinic, stl_payments: list[Payment]
    ):
        service = SettlementService(db)
        s1 = await service.generate_monthly_settlement(stl_clinic.id, 2026, 1)
        await db.flush()
        s2 = await service.generate_monthly_settlement(stl_clinic.id, 2026, 1)
        assert s1.id == s2.id

    @pytest.mark.asyncio
    async def test_different_commission_rate(
        self, db: AsyncSession, stl_clinic_b: Clinic
    ):
        # Create a payment for clinic B
        customer = Customer(
            id=uuid.uuid4(),
            clinic_id=stl_clinic_b.id,
            messenger_type="telegram",
            messenger_user_id="stl-tg-b",
        )
        db.add(customer)
        p = Payment(
            id=uuid.uuid4(),
            clinic_id=stl_clinic_b.id,
            customer_id=customer.id,
            payment_type="full",
            amount=Decimal("200000.00"),
            currency="KRW",
            status="completed",
            paid_at=datetime(2026, 2, 10, tzinfo=timezone.utc),
        )
        db.add(p)
        await db.commit()

        service = SettlementService(db)
        settlement = await service.generate_monthly_settlement(
            stl_clinic_b.id, 2026, 2
        )
        # 15% commission on 200,000 = 30,000
        assert settlement.commission_rate == Decimal("15.00")
        assert settlement.commission_amount == Decimal("30000.00")
        # VAT 10% of 30,000 = 3,000
        assert settlement.vat_amount == Decimal("3000.00")
        assert settlement.total_settlement == Decimal("33000.00")


class TestGenerateAllSettlements:
    @pytest.mark.asyncio
    async def test_generates_for_all_active_clinics(
        self,
        db: AsyncSession,
        stl_clinic: Clinic,
        stl_clinic_b: Clinic,
        stl_payments: list[Payment],
    ):
        service = SettlementService(db)
        settlements = await service.generate_all_settlements(2026, 1)
        # At least stl_clinic should have settlement (stl_clinic_b has no Jan payments)
        assert len(settlements) >= 1
        clinic_ids = {s.clinic_id for s in settlements}
        assert stl_clinic.id in clinic_ids
