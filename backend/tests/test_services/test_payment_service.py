import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.payment import Payment
from app.payment.base import PaymentResult
from app.services.payment_service import PaymentService


# --- Fixtures ---
@pytest_asyncio.fixture
async def ps_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="서비스의원", slug="ps-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def ps_customer(db: AsyncSession, ps_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=ps_clinic.id,
        messenger_type="telegram",
        messenger_user_id="ps-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def ps_booking(
    db: AsyncSession, ps_clinic: Clinic, ps_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=ps_clinic.id,
        customer_id=ps_customer.id,
        booking_date=date(2026, 5, 1),
        booking_time=time(10, 0),
        status="pending",
        total_amount=Decimal("500000"),
        deposit_amount=Decimal("100000"),
        remaining_amount=Decimal("400000"),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def ps_confirmed_booking(
    db: AsyncSession, ps_clinic: Clinic, ps_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=ps_clinic.id,
        customer_id=ps_customer.id,
        booking_date=date(2026, 5, 5),
        booking_time=time(14, 0),
        status="confirmed",
        total_amount=Decimal("300000"),
        deposit_amount=Decimal("100000"),
        remaining_amount=Decimal("200000"),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


# --- Tests ---
class TestCreatePaymentLink:
    @pytest.mark.asyncio
    async def test_creates_payment_with_link(
        self, db: AsyncSession, ps_clinic: Clinic, ps_customer: Customer
    ):
        service = PaymentService(db)
        payment = await service.create_payment_link(
            clinic_id=ps_clinic.id,
            booking_id=None,
            customer_id=ps_customer.id,
            payment_type="full",
            amount=50000,
            currency="KRW",
            provider_type="stub",
        )
        assert payment.status == "link_sent"
        assert payment.payment_link is not None
        assert payment.pg_provider == "stub"

    @pytest.mark.asyncio
    async def test_creates_payment_with_booking(
        self,
        db: AsyncSession,
        ps_clinic: Clinic,
        ps_customer: Customer,
        ps_booking: Booking,
    ):
        service = PaymentService(db)
        payment = await service.create_payment_link(
            clinic_id=ps_clinic.id,
            booking_id=ps_booking.id,
            customer_id=ps_customer.id,
            payment_type="deposit",
            amount=100000,
            currency="KRW",
            provider_type="stub",
        )
        assert payment.booking_id == ps_booking.id
        assert payment.payment_type == "deposit"

    @pytest.mark.asyncio
    async def test_creates_with_auto_routing(
        self, db: AsyncSession, ps_clinic: Clinic, ps_customer: Customer
    ):
        service = PaymentService(db)
        payment = await service.create_payment_link(
            clinic_id=ps_clinic.id,
            booking_id=None,
            customer_id=ps_customer.id,
            payment_type="full",
            amount=30000,
            currency="KRW",
        )
        # Falls back to stripe when no routing info
        assert payment.pg_provider == "stripe"
        assert payment.payment_link is not None


class TestHandleWebhook:
    @pytest.mark.asyncio
    async def test_completes_payment(
        self,
        db: AsyncSession,
        ps_clinic: Clinic,
        ps_customer: Customer,
    ):
        # Create a payment first
        service = PaymentService(db)
        payment = await service.create_payment_link(
            clinic_id=ps_clinic.id,
            booking_id=None,
            customer_id=ps_customer.id,
            payment_type="full",
            amount=50000,
            currency="KRW",
            provider_type="stub",
        )
        pg_id = payment.pg_payment_id

        result = PaymentResult(
            provider_payment_id=pg_id,
            status="completed",
            amount=50000,
            currency="KRW",
            payment_method="card",
            paid_at=datetime.now(timezone.utc),
        )
        updated = await service.handle_webhook("stub", result)
        assert updated.status == "completed"
        assert updated.payment_method == "card"
        assert updated.paid_at is not None

    @pytest.mark.asyncio
    async def test_confirms_booking_on_payment(
        self,
        db: AsyncSession,
        ps_clinic: Clinic,
        ps_customer: Customer,
        ps_booking: Booking,
    ):
        service = PaymentService(db)
        payment = await service.create_payment_link(
            clinic_id=ps_clinic.id,
            booking_id=ps_booking.id,
            customer_id=ps_customer.id,
            payment_type="deposit",
            amount=100000,
            currency="KRW",
            provider_type="stub",
        )

        result = PaymentResult(
            provider_payment_id=payment.pg_payment_id,
            status="completed",
            amount=100000,
            currency="KRW",
            payment_method="card",
            paid_at=datetime.now(timezone.utc),
        )
        await service.handle_webhook("stub", result)

        # Booking should be confirmed
        await db.refresh(ps_booking)
        assert ps_booking.status == "confirmed"

    @pytest.mark.asyncio
    async def test_idempotent_completed(
        self,
        db: AsyncSession,
        ps_clinic: Clinic,
        ps_customer: Customer,
    ):
        service = PaymentService(db)
        payment = await service.create_payment_link(
            clinic_id=ps_clinic.id,
            booking_id=None,
            customer_id=ps_customer.id,
            payment_type="full",
            amount=50000,
            currency="KRW",
            provider_type="stub",
        )

        result = PaymentResult(
            provider_payment_id=payment.pg_payment_id,
            status="completed",
            amount=50000,
            currency="KRW",
            paid_at=datetime.now(timezone.utc),
        )
        # First call
        await service.handle_webhook("stub", result)
        # Second call — idempotent
        updated = await service.handle_webhook("stub", result)
        assert updated.status == "completed"

    @pytest.mark.asyncio
    async def test_not_found_raises(self, db: AsyncSession):
        service = PaymentService(db)
        result = PaymentResult(
            provider_payment_id="nonexistent_id",
            status="completed",
            amount=50000,
            currency="KRW",
        )
        with pytest.raises(Exception, match="Payment not found"):
            await service.handle_webhook("stub", result)


class TestRequestRemaining:
    @pytest.mark.asyncio
    async def test_success(
        self,
        db: AsyncSession,
        ps_clinic: Clinic,
        ps_customer: Customer,
        ps_confirmed_booking: Booking,
    ):
        service = PaymentService(db)
        payment = await service.request_remaining(
            clinic_id=ps_clinic.id,
            booking_id=ps_confirmed_booking.id,
            customer_id=ps_customer.id,
            amount=200000,
            currency="KRW",
        )
        assert payment.payment_type == "remaining"
        assert payment.status == "link_sent"

    @pytest.mark.asyncio
    async def test_pending_booking_rejected(
        self,
        db: AsyncSession,
        ps_clinic: Clinic,
        ps_customer: Customer,
        ps_booking: Booking,
    ):
        service = PaymentService(db)
        with pytest.raises(Exception, match="must be confirmed"):
            await service.request_remaining(
                clinic_id=ps_clinic.id,
                booking_id=ps_booking.id,
                customer_id=ps_customer.id,
                amount=400000,
                currency="KRW",
            )

    @pytest.mark.asyncio
    async def test_nonexistent_booking_rejected(
        self, db: AsyncSession, ps_clinic: Clinic, ps_customer: Customer
    ):
        service = PaymentService(db)
        with pytest.raises(Exception, match="Booking not found"):
            await service.request_remaining(
                clinic_id=ps_clinic.id,
                booking_id=uuid.uuid4(),
                customer_id=ps_customer.id,
                amount=100000,
                currency="KRW",
            )
