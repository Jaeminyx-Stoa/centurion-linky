import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.booking import Booking
from app.models.crm_event import CRMEvent
from app.models.payment import Payment

# Default CRM timeline offsets (aftercare/survey_2/survey_3/revisit moved to FollowupRules)
_TIMELINE = [
    ("receipt", timedelta(minutes=0)),
    ("review_request", timedelta(minutes=30)),
    ("survey_1", timedelta(hours=6)),
]


class CRMService:
    """Orchestrates CRM event scheduling and lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_crm_timeline(self, payment_id: uuid.UUID) -> list[CRMEvent]:
        """Schedule the full CRM timeline when payment is completed."""
        # Look up payment
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            raise NotFoundError("Payment not found")

        now = datetime.now(timezone.utc)
        events = []
        for event_type, offset in _TIMELINE:
            event = CRMEvent(
                id=uuid.uuid4(),
                clinic_id=payment.clinic_id,
                customer_id=payment.customer_id,
                payment_id=payment.id,
                booking_id=payment.booking_id,
                event_type=event_type,
                scheduled_at=now + offset,
                status="scheduled",
            )
            self.db.add(event)
            events.append(event)

        await self.db.flush()
        return events

    async def cancel_event(
        self, event_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> CRMEvent:
        """Cancel a scheduled CRM event."""
        result = await self.db.execute(
            select(CRMEvent).where(
                CRMEvent.id == event_id,
                CRMEvent.clinic_id == clinic_id,
            )
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("CRM event not found")
        if event.status != "scheduled":
            raise BadRequestError(
                f"Cannot cancel event with status '{event.status}'"
            )
        event.status = "cancelled"
        await self.db.flush()
        return event

    async def get_due_events(self) -> list[CRMEvent]:
        """Get events that are due for execution (scheduled_at <= now)."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(CRMEvent).where(
                CRMEvent.status == "scheduled",
                CRMEvent.scheduled_at <= now,
            )
        )
        return list(result.scalars().all())

    async def mark_sent(self, event_id: uuid.UUID) -> CRMEvent:
        """Mark event as sent after execution."""
        result = await self.db.execute(
            select(CRMEvent).where(CRMEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("CRM event not found")
        event.status = "sent"
        event.executed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return event

    async def mark_failed(
        self, event_id: uuid.UUID, error: str | None = None
    ) -> CRMEvent:
        """Mark event as failed after execution error."""
        result = await self.db.execute(
            select(CRMEvent).where(CRMEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("CRM event not found")
        event.status = "failed"
        event.executed_at = datetime.now(timezone.utc)
        if error:
            event.response = {"error": error}
        await self.db.flush()
        return event

    async def cancel_remaining_for_booking(
        self, booking_id: uuid.UUID
    ) -> int:
        """Cancel all scheduled events for a booking (e.g. when booking is cancelled)."""
        result = await self.db.execute(
            select(CRMEvent).where(
                CRMEvent.booking_id == booking_id,
                CRMEvent.status == "scheduled",
            )
        )
        events = list(result.scalars().all())
        for event in events:
            event.status = "cancelled"
        await self.db.flush()
        return len(events)
