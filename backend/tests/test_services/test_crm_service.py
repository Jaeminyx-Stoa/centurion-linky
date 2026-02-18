import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.crm_event import CRMEvent
from app.models.customer import Customer
from app.models.payment import Payment
from app.services.crm_service import CRMService


# --- Fixtures ---
@pytest_asyncio.fixture
async def cs_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="서비스CRM의원", slug="cs-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def cs_customer(db: AsyncSession, cs_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=cs_clinic.id,
        messenger_type="telegram",
        messenger_user_id="cs-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def cs_booking(
    db: AsyncSession, cs_clinic: Clinic, cs_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=cs_clinic.id,
        customer_id=cs_customer.id,
        booking_date=date(2026, 8, 1),
        booking_time=time(10, 0),
        status="confirmed",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def cs_payment(
    db: AsyncSession,
    cs_clinic: Clinic,
    cs_customer: Customer,
    cs_booking: Booking,
) -> Payment:
    payment = Payment(
        id=uuid.uuid4(),
        clinic_id=cs_clinic.id,
        booking_id=cs_booking.id,
        customer_id=cs_customer.id,
        payment_type="deposit",
        amount=100000,
        currency="KRW",
        status="completed",
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


# --- Tests ---
class TestScheduleCRMTimeline:
    @pytest.mark.asyncio
    async def test_creates_7_events(
        self, db: AsyncSession, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)
        assert len(events) == 7

    @pytest.mark.asyncio
    async def test_event_types(
        self, db: AsyncSession, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)
        types = [e.event_type for e in events]
        assert types == [
            "receipt",
            "review_request",
            "aftercare",
            "survey_1",
            "survey_2",
            "survey_3",
            "revisit_reminder",
        ]

    @pytest.mark.asyncio
    async def test_all_events_scheduled_status(
        self, db: AsyncSession, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)
        assert all(e.status == "scheduled" for e in events)

    @pytest.mark.asyncio
    async def test_events_linked_to_payment_and_booking(
        self, db: AsyncSession, cs_payment: Payment, cs_booking: Booking
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)
        assert all(e.payment_id == cs_payment.id for e in events)
        assert all(e.booking_id == cs_booking.id for e in events)

    @pytest.mark.asyncio
    async def test_payment_not_found(self, db: AsyncSession):
        service = CRMService(db)
        with pytest.raises(Exception, match="Payment not found"):
            await service.schedule_crm_timeline(uuid.uuid4())


class TestCancelEvent:
    @pytest.mark.asyncio
    async def test_cancel_scheduled(
        self, db: AsyncSession, cs_clinic: Clinic, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)

        cancelled = await service.cancel_event(events[2].id, cs_clinic.id)
        assert cancelled.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_non_scheduled_fails(
        self, db: AsyncSession, cs_clinic: Clinic, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)

        # Mark one as sent first
        await service.mark_sent(events[0].id)

        with pytest.raises(Exception, match="Cannot cancel"):
            await service.cancel_event(events[0].id, cs_clinic.id)


class TestGetDueEvents:
    @pytest.mark.asyncio
    async def test_returns_due_events(
        self, db: AsyncSession, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)

        # receipt (offset=0) should be due immediately
        due = await service.get_due_events()
        due_types = [e.event_type for e in due]
        assert "receipt" in due_types


class TestMarkSent:
    @pytest.mark.asyncio
    async def test_mark_sent(
        self, db: AsyncSession, cs_payment: Payment
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)

        sent = await service.mark_sent(events[0].id)
        assert sent.status == "sent"
        assert sent.executed_at is not None


class TestCancelRemainingForBooking:
    @pytest.mark.asyncio
    async def test_cancels_all_scheduled(
        self, db: AsyncSession, cs_payment: Payment, cs_booking: Booking
    ):
        service = CRMService(db)
        events = await service.schedule_crm_timeline(cs_payment.id)

        # Mark first as sent
        await service.mark_sent(events[0].id)

        # Cancel remaining for booking
        count = await service.cancel_remaining_for_booking(cs_booking.id)
        assert count == 6  # 7 total - 1 sent = 6 cancelled
