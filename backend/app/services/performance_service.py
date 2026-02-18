import uuid
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.consultation_performance import ConsultationPerformance
from app.models.conversation import Conversation
from app.models.payment import Payment


def rate_to_score(
    rate: float, thresholds: list[tuple[float, float]], default: float = 5.0
) -> float:
    """Convert a percentage rate to a score using threshold brackets."""
    for threshold, score in thresholds:
        if rate >= threshold:
            return score
    return default


class PerformanceService:
    """Monthly consultation performance calculation."""

    # Booking conversion thresholds (max 30 points)
    BOOKING_THRESHOLDS = [
        (90, 30), (80, 25), (70, 20), (60, 15), (50, 10),
    ]

    # Payment conversion thresholds (max 30 points)
    PAYMENT_THRESHOLDS = [
        (95, 30), (90, 25), (85, 20), (80, 15), (70, 10),
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_performance(
        self, clinic_id: uuid.UUID, year: int, month: int
    ) -> ConsultationPerformance:
        """Calculate or return existing performance for a clinic's period."""
        # Check existing (idempotent)
        existing = await self.db.execute(
            select(ConsultationPerformance).where(
                ConsultationPerformance.clinic_id == clinic_id,
                ConsultationPerformance.period_year == year,
                ConsultationPerformance.period_month == month,
            )
        )
        perf = existing.scalar_one_or_none()
        if perf is not None:
            return perf

        # Count consultations (conversations created in period)
        consult_count = await self._count(
            Conversation.id,
            Conversation.clinic_id == clinic_id,
            extract("year", Conversation.created_at) == year,
            extract("month", Conversation.created_at) == month,
        )

        # Count bookings in period
        booking_count = await self._count(
            Booking.id,
            Booking.clinic_id == clinic_id,
            extract("year", Booking.created_at) == year,
            extract("month", Booking.created_at) == month,
        )

        # Count completed payments in period
        payment_count = await self._count(
            Payment.id,
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            extract("year", Payment.paid_at) == year,
            extract("month", Payment.paid_at) == month,
        )

        # Calculate rates
        booking_rate = (
            (booking_count / consult_count * 100) if consult_count > 0 else 0.0
        )
        payment_rate = (
            (payment_count / booking_count * 100) if booking_count > 0 else 0.0
        )

        # Calculate scores
        # Sales mix score simplified: (booking_count > 0 gives base 20, scaled by payment)
        sales_mix_score = min(
            Decimal(str(round((payment_count / max(consult_count, 1)) * 40, 2))),
            Decimal("40.00"),
        )
        booking_score = Decimal(
            str(rate_to_score(booking_rate, self.BOOKING_THRESHOLDS))
        )
        payment_score = Decimal(
            str(rate_to_score(payment_rate, self.PAYMENT_THRESHOLDS))
        )
        total_score = sales_mix_score + booking_score + payment_score

        perf = ConsultationPerformance(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            period_year=year,
            period_month=month,
            total_score=total_score,
            sales_mix_score=sales_mix_score,
            booking_conversion_score=booking_score,
            booking_conversion_rate=Decimal(str(round(booking_rate, 2))),
            payment_conversion_score=payment_score,
            payment_conversion_rate=Decimal(str(round(payment_rate, 2))),
            total_consultations=consult_count,
            total_bookings=booking_count,
            total_payments=payment_count,
        )
        self.db.add(perf)
        await self.db.flush()
        return perf

    async def _count(self, column, *filters) -> int:
        result = await self.db.execute(
            select(func.count(column)).where(*filters)
        )
        return result.scalar() or 0
