from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.booking import Booking
from app.models.consultation_performance import ConsultationPerformance
from app.models.conversation import Conversation
from app.models.payment import Payment
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    ConsultationPerformanceResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clinic_id = current_user.clinic_id

    # Conversations
    conv_result = await db.execute(
        select(
            func.count(Conversation.id).label("total"),
            func.count(Conversation.id)
            .filter(Conversation.status == "active")
            .label("active"),
            func.count(Conversation.id)
            .filter(Conversation.status == "resolved")
            .label("resolved"),
        ).where(Conversation.clinic_id == clinic_id)
    )
    conv_row = conv_result.one()

    # Bookings
    booking_result = await db.execute(
        select(func.count(Booking.id)).where(Booking.clinic_id == clinic_id)
    )
    total_bookings = booking_result.scalar() or 0

    # Payments
    payment_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.clinic_id == clinic_id)
    )
    total_payments = payment_result.scalar() or 0

    return AnalyticsOverviewResponse(
        total_conversations=conv_row.total,
        active_conversations=conv_row.active,
        resolved_conversations=conv_row.resolved,
        total_bookings=total_bookings,
        total_payments=total_payments,
    )


@router.get(
    "/consultation-performance",
    response_model=ConsultationPerformanceResponse,
)
async def get_consultation_performance(
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConsultationPerformance).where(
            ConsultationPerformance.clinic_id == current_user.clinic_id,
            ConsultationPerformance.period_year == year,
            ConsultationPerformance.period_month == month,
        )
    )
    perf = result.scalar_one_or_none()
    if perf is None:
        raise NotFoundError("Performance data not found for this period")
    return perf
