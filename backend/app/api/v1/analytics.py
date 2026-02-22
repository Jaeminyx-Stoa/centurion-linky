from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.core.cache import cache_get, cache_set
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.ab_test import ABTest, ABTestResult, ABTestVariant
from app.models.booking import Booking
from app.models.consultation_performance import ConsultationPerformance
from app.models.conversation import Conversation
from app.models.message import Message
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
    cache_key = f"analytics:overview:{clinic_id}"

    # Check cache first
    cached = await cache_get(cache_key)
    if cached:
        return AnalyticsOverviewResponse(**cached)

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

    result = AnalyticsOverviewResponse(
        total_conversations=conv_row.total,
        active_conversations=conv_row.active,
        resolved_conversations=conv_row.resolved,
        total_bookings=total_bookings,
        total_payments=total_payments,
    )

    # Cache for 5 minutes
    await cache_set(cache_key, result.model_dump(), ttl_seconds=300)
    return result


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


@router.get("/ai-feedback")
async def get_ai_feedback_stats(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI response feedback statistics for the last N days."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    # Query all AI messages with feedback in the period
    result = await db.execute(
        select(Message.ai_metadata).where(
            Message.clinic_id == clinic_id,
            Message.sender_type == "ai",
            Message.ai_metadata.isnot(None),
            func.date(Message.created_at) >= cutoff,
        )
    )
    rows = result.scalars().all()

    up_count = 0
    down_count = 0
    for metadata in rows:
        if not isinstance(metadata, dict):
            continue
        feedback = metadata.get("feedback")
        if feedback:
            if feedback.get("rating") == "up":
                up_count += 1
            elif feedback.get("rating") == "down":
                down_count += 1

    total = up_count + down_count
    return {
        "days": days,
        "total_feedback": total,
        "up": up_count,
        "down": down_count,
        "up_ratio": round(up_count / total, 3) if total > 0 else None,
    }


@router.get("/conversations")
async def get_conversation_analytics(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Conversation analytics: daily volume, AI vs manual, avg messages per conversation."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    # Daily conversation counts
    daily_result = await db.execute(
        select(
            func.date(Conversation.created_at).label("day"),
            func.count(Conversation.id).label("total"),
            func.count(Conversation.id)
            .filter(Conversation.ai_mode.is_(True))
            .label("ai_mode"),
            func.count(Conversation.id)
            .filter(Conversation.ai_mode.is_(False))
            .label("manual_mode"),
        )
        .where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
    )
    daily_data = [
        {
            "date": str(row.day),
            "total": row.total,
            "ai_mode": row.ai_mode,
            "manual_mode": row.manual_mode,
        }
        for row in daily_result.all()
    ]

    # Status distribution
    status_result = await db.execute(
        select(
            Conversation.status,
            func.count(Conversation.id).label("count"),
        )
        .where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
        .group_by(Conversation.status)
    )
    status_distribution = {row.status: row.count for row in status_result.all()}

    # Average messages per conversation
    avg_result = await db.execute(
        select(func.avg(func.count(Message.id)))
        .select_from(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
        .group_by(Message.conversation_id)
    )
    avg_messages = avg_result.scalar()

    # Average satisfaction
    sat_result = await db.execute(
        select(func.avg(Conversation.satisfaction_score)).where(
            Conversation.clinic_id == clinic_id,
            Conversation.satisfaction_score.isnot(None),
            func.date(Conversation.created_at) >= cutoff,
        )
    )
    avg_satisfaction = sat_result.scalar()

    return {
        "days": days,
        "daily": daily_data,
        "status_distribution": status_distribution,
        "avg_messages_per_conversation": round(float(avg_messages), 1) if avg_messages else 0,
        "avg_satisfaction_score": round(float(avg_satisfaction), 1) if avg_satisfaction else None,
    }


@router.get("/sales-performance")
async def get_sales_performance(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sales funnel analytics: conversations → bookings → payments conversion."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    # Total conversations in period
    conv_count_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
    )
    total_conversations = conv_count_result.scalar() or 0

    # Total bookings in period
    booking_count_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.clinic_id == clinic_id,
            func.date(Booking.created_at) >= cutoff,
        )
    )
    total_bookings = booking_count_result.scalar() or 0

    # Total payments in period
    payment_result = await db.execute(
        select(
            func.count(Payment.id).label("count"),
            func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
        ).where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
    )
    payment_row = payment_result.one()

    # Daily revenue trend
    revenue_result = await db.execute(
        select(
            func.date(Payment.paid_at).label("day"),
            func.count(Payment.id).label("count"),
            func.sum(Payment.amount).label("amount"),
        )
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            Payment.paid_at.isnot(None),
            func.date(Payment.paid_at) >= cutoff,
        )
        .group_by(func.date(Payment.paid_at))
        .order_by(func.date(Payment.paid_at))
    )
    revenue_daily = [
        {
            "date": str(row.day),
            "count": row.count,
            "amount": float(row.amount or 0),
        }
        for row in revenue_result.all()
    ]

    booking_rate = round(total_bookings / total_conversations * 100, 1) if total_conversations > 0 else 0
    payment_rate = round(payment_row.count / total_bookings * 100, 1) if total_bookings > 0 else 0

    return {
        "days": days,
        "funnel": {
            "conversations": total_conversations,
            "bookings": total_bookings,
            "payments": payment_row.count,
            "booking_conversion_rate": booking_rate,
            "payment_conversion_rate": payment_rate,
        },
        "revenue": {
            "total_amount": float(payment_row.total_amount),
            "daily": revenue_daily,
        },
    }


@router.get("/ab-tests")
async def get_ab_test_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A/B test analytics: results summary per test with variant-level breakdown."""
    clinic_id = current_user.clinic_id

    # Load all tests with variants
    tests_result = await db.execute(
        select(ABTest)
        .options(selectinload(ABTest.variants))
        .where(ABTest.clinic_id == clinic_id)
        .order_by(ABTest.created_at.desc())
    )
    tests = tests_result.scalars().all()

    items = []
    for test in tests:
        # Get result counts per variant
        variant_stats = []
        for variant in test.variants:
            result = await db.execute(
                select(
                    ABTestResult.outcome,
                    func.count(ABTestResult.id).label("count"),
                ).where(
                    ABTestResult.ab_test_id == test.id,
                    ABTestResult.variant_id == variant.id,
                ).group_by(ABTestResult.outcome)
            )
            outcome_counts = {row.outcome: row.count for row in result.all()}
            total = sum(outcome_counts.values())
            variant_stats.append({
                "variant_id": str(variant.id),
                "variant_name": variant.name,
                "weight": variant.weight,
                "total_assignments": total,
                "outcomes": outcome_counts,
            })

        items.append({
            "id": str(test.id),
            "name": test.name,
            "test_type": test.test_type,
            "status": test.status,
            "is_active": test.is_active,
            "started_at": test.started_at.isoformat() if test.started_at else None,
            "ended_at": test.ended_at.isoformat() if test.ended_at else None,
            "variants": variant_stats,
        })

    return {"tests": items}
