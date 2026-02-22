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
from app.models.clinic_procedure import ClinicProcedure
from app.models.consultation_performance import ConsultationPerformance
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.models.procedure import Procedure
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


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    days: int = Query(default=30, ge=1, le=365),
    group_by: str = Query(default="nationality", pattern="^(nationality|channel|both)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Conversion funnel: conversations → bookings → payments, grouped by nationality/channel/both."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    if group_by == "nationality":
        groups = await _funnel_by_nationality(db, clinic_id, cutoff)
    elif group_by == "channel":
        groups = await _funnel_by_channel(db, clinic_id, cutoff)
    else:
        groups = await _funnel_by_both(db, clinic_id, cutoff)

    # Totals
    total_conversations = sum(g["conversations"] for g in groups)
    total_bookings = sum(g["bookings"] for g in groups)
    total_payments = sum(g["payments"] for g in groups)

    return {
        "days": days,
        "group_by": group_by,
        "groups": groups,
        "totals": {
            "conversations": total_conversations,
            "bookings": total_bookings,
            "payments": total_payments,
            "booking_rate": round(total_bookings / total_conversations * 100, 1) if total_conversations > 0 else 0,
            "payment_rate": round(total_payments / total_bookings * 100, 1) if total_bookings > 0 else 0,
        },
    }


async def _funnel_by_nationality(db: AsyncSession, clinic_id, cutoff):
    # Conversations per country
    conv_result = await db.execute(
        select(
            Customer.country_code,
            func.count(func.distinct(Conversation.customer_id)).label("conversations"),
        )
        .join(Customer, Conversation.customer_id == Customer.id)
        .where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
        .group_by(Customer.country_code)
    )
    conv_data = {row.country_code or "unknown": row.conversations for row in conv_result.all()}

    # Bookings per country
    booking_result = await db.execute(
        select(
            Customer.country_code,
            func.count(func.distinct(Booking.customer_id)).label("bookings"),
        )
        .join(Customer, Booking.customer_id == Customer.id)
        .where(
            Booking.clinic_id == clinic_id,
            func.date(Booking.created_at) >= cutoff,
        )
        .group_by(Customer.country_code)
    )
    booking_data = {row.country_code or "unknown": row.bookings for row in booking_result.all()}

    # Payments per country
    payment_result = await db.execute(
        select(
            Customer.country_code,
            func.count(func.distinct(Payment.customer_id)).label("payments"),
        )
        .join(Customer, Payment.customer_id == Customer.id)
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
        .group_by(Customer.country_code)
    )
    payment_data = {row.country_code or "unknown": row.payments for row in payment_result.all()}

    all_dims = set(conv_data.keys()) | set(booking_data.keys())
    groups = []
    for dim in sorted(all_dims):
        convs = conv_data.get(dim, 0)
        bkgs = booking_data.get(dim, 0)
        pmts = payment_data.get(dim, 0)
        groups.append({
            "dimension": dim,
            "conversations": convs,
            "bookings": bkgs,
            "payments": pmts,
            "booking_rate": round(bkgs / convs * 100, 1) if convs > 0 else 0,
            "payment_rate": round(pmts / bkgs * 100, 1) if bkgs > 0 else 0,
        })
    return groups


async def _funnel_by_channel(db: AsyncSession, clinic_id, cutoff):
    conv_result = await db.execute(
        select(
            MessengerAccount.messenger_type,
            func.count(func.distinct(Conversation.customer_id)).label("conversations"),
        )
        .join(MessengerAccount, Conversation.messenger_account_id == MessengerAccount.id)
        .where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
        .group_by(MessengerAccount.messenger_type)
    )
    conv_data = {row.messenger_type: row.conversations for row in conv_result.all()}

    # For bookings/payments by channel, join through conversation
    booking_result = await db.execute(
        select(
            MessengerAccount.messenger_type,
            func.count(func.distinct(Booking.customer_id)).label("bookings"),
        )
        .select_from(Booking)
        .join(Conversation, Booking.conversation_id == Conversation.id)
        .join(MessengerAccount, Conversation.messenger_account_id == MessengerAccount.id)
        .where(
            Booking.clinic_id == clinic_id,
            func.date(Booking.created_at) >= cutoff,
        )
        .group_by(MessengerAccount.messenger_type)
    )
    booking_data = {row.messenger_type: row.bookings for row in booking_result.all()}

    payment_result = await db.execute(
        select(
            MessengerAccount.messenger_type,
            func.count(func.distinct(Payment.customer_id)).label("payments"),
        )
        .select_from(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .join(Conversation, Booking.conversation_id == Conversation.id)
        .join(MessengerAccount, Conversation.messenger_account_id == MessengerAccount.id)
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
        .group_by(MessengerAccount.messenger_type)
    )
    payment_data = {row.messenger_type: row.payments for row in payment_result.all()}

    all_dims = set(conv_data.keys()) | set(booking_data.keys())
    groups = []
    for dim in sorted(all_dims):
        convs = conv_data.get(dim, 0)
        bkgs = booking_data.get(dim, 0)
        pmts = payment_data.get(dim, 0)
        groups.append({
            "dimension": dim,
            "conversations": convs,
            "bookings": bkgs,
            "payments": pmts,
            "booking_rate": round(bkgs / convs * 100, 1) if convs > 0 else 0,
            "payment_rate": round(pmts / bkgs * 100, 1) if bkgs > 0 else 0,
        })
    return groups


async def _funnel_by_both(db: AsyncSession, clinic_id, cutoff):
    conv_result = await db.execute(
        select(
            Customer.country_code,
            MessengerAccount.messenger_type,
            func.count(func.distinct(Conversation.customer_id)).label("conversations"),
        )
        .join(Customer, Conversation.customer_id == Customer.id)
        .join(MessengerAccount, Conversation.messenger_account_id == MessengerAccount.id)
        .where(
            Conversation.clinic_id == clinic_id,
            func.date(Conversation.created_at) >= cutoff,
        )
        .group_by(Customer.country_code, MessengerAccount.messenger_type)
    )
    conv_data = {}
    for row in conv_result.all():
        key = f"{row.country_code or 'unknown'}|{row.messenger_type}"
        conv_data[key] = row.conversations

    booking_result = await db.execute(
        select(
            Customer.country_code,
            MessengerAccount.messenger_type,
            func.count(func.distinct(Booking.customer_id)).label("bookings"),
        )
        .select_from(Booking)
        .join(Customer, Booking.customer_id == Customer.id)
        .join(Conversation, Booking.conversation_id == Conversation.id)
        .join(MessengerAccount, Conversation.messenger_account_id == MessengerAccount.id)
        .where(
            Booking.clinic_id == clinic_id,
            func.date(Booking.created_at) >= cutoff,
        )
        .group_by(Customer.country_code, MessengerAccount.messenger_type)
    )
    booking_data = {}
    for row in booking_result.all():
        key = f"{row.country_code or 'unknown'}|{row.messenger_type}"
        booking_data[key] = row.bookings

    payment_result = await db.execute(
        select(
            Customer.country_code,
            MessengerAccount.messenger_type,
            func.count(func.distinct(Payment.customer_id)).label("payments"),
        )
        .select_from(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .join(Customer, Payment.customer_id == Customer.id)
        .join(Conversation, Booking.conversation_id == Conversation.id)
        .join(MessengerAccount, Conversation.messenger_account_id == MessengerAccount.id)
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
        .group_by(Customer.country_code, MessengerAccount.messenger_type)
    )
    payment_data = {}
    for row in payment_result.all():
        key = f"{row.country_code or 'unknown'}|{row.messenger_type}"
        payment_data[key] = row.payments

    all_dims = set(conv_data.keys()) | set(booking_data.keys())
    groups = []
    for dim in sorted(all_dims):
        convs = conv_data.get(dim, 0)
        bkgs = booking_data.get(dim, 0)
        pmts = payment_data.get(dim, 0)
        groups.append({
            "dimension": dim,
            "conversations": convs,
            "bookings": bkgs,
            "payments": pmts,
            "booking_rate": round(bkgs / convs * 100, 1) if convs > 0 else 0,
            "payment_rate": round(pmts / bkgs * 100, 1) if bkgs > 0 else 0,
        })
    return groups


# --- Revenue / Margin deep analytics ---


@router.get("/procedure-profitability")
async def get_procedure_profitability(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-procedure revenue, material cost, and margin analysis."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    result = await db.execute(
        select(
            Procedure.id.label("procedure_id"),
            Procedure.name_ko.label("procedure_name"),
            func.count(Payment.id).label("case_count"),
            func.coalesce(func.sum(Payment.amount), 0).label("total_revenue"),
            func.coalesce(func.avg(Payment.amount), 0).label("avg_ticket"),
            ClinicProcedure.material_cost,
        )
        .select_from(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .join(ClinicProcedure, Booking.clinic_procedure_id == ClinicProcedure.id)
        .join(Procedure, ClinicProcedure.procedure_id == Procedure.id)
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
        .group_by(Procedure.id, Procedure.name_ko, ClinicProcedure.material_cost)
        .order_by(func.sum(Payment.amount).desc())
    )
    rows = result.all()

    procedures = []
    for row in rows:
        revenue = float(row.total_revenue)
        material = float(row.material_cost or 0) * row.case_count
        margin = revenue - material
        margin_rate = round(margin / revenue * 100, 1) if revenue > 0 else 0
        procedures.append({
            "procedure_id": str(row.procedure_id),
            "procedure_name": row.procedure_name,
            "case_count": row.case_count,
            "total_revenue": revenue,
            "avg_ticket": round(float(row.avg_ticket), 0),
            "total_material_cost": material,
            "gross_margin": margin,
            "margin_rate": margin_rate,
        })

    procedures.sort(key=lambda x: x["margin_rate"], reverse=True)

    return {"days": days, "procedures": procedures}


@router.get("/customer-lifetime-value")
async def get_customer_lifetime_value(
    days: int = Query(default=365, ge=30, le=1095),
    top_n: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Customer lifetime value analysis with nationality breakdown."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    result = await db.execute(
        select(
            Customer.id.label("customer_id"),
            Customer.name.label("customer_name"),
            Customer.country_code,
            func.coalesce(func.sum(Payment.amount), 0).label("total_payments"),
            func.count(func.distinct(Booking.booking_date)).label("visit_count"),
            func.min(Booking.booking_date).label("first_visit"),
            func.max(Booking.booking_date).label("last_visit"),
            func.coalesce(func.avg(Payment.amount), 0).label("avg_ticket"),
        )
        .select_from(Customer)
        .join(Payment, Payment.customer_id == Customer.id)
        .join(Booking, Payment.booking_id == Booking.id)
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
        .group_by(Customer.id, Customer.name, Customer.country_code)
        .order_by(func.sum(Payment.amount).desc())
        .limit(top_n)
    )
    rows = result.all()

    customers = []
    for row in rows:
        total = float(row.total_payments)
        first_visit = row.first_visit
        last_visit = row.last_visit
        months_active = 1
        if first_visit and last_visit and last_visit > first_visit:
            delta = last_visit - first_visit
            months_active = max(1, delta.days / 30)
        predicted_annual = round(total / months_active * 12, 0)

        customers.append({
            "customer_id": str(row.customer_id),
            "customer_name": row.customer_name,
            "country_code": row.country_code or "unknown",
            "total_payments": total,
            "visit_count": row.visit_count,
            "first_visit": str(first_visit) if first_visit else None,
            "last_visit": str(last_visit) if last_visit else None,
            "avg_ticket": round(float(row.avg_ticket), 0),
            "predicted_annual_value": predicted_annual,
        })

    # Nationality average CLV
    nat_agg_result = await db.execute(
        select(
            Customer.country_code,
            func.sum(Payment.amount).label("customer_total"),
        )
        .select_from(Customer)
        .join(Payment, Payment.customer_id == Customer.id)
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            func.date(Payment.created_at) >= cutoff,
        )
        .group_by(Customer.id, Customer.country_code)
    )
    nat_data: dict[str, list[float]] = {}
    for row in nat_agg_result.all():
        cc = row.country_code or "unknown"
        if cc not in nat_data:
            nat_data[cc] = []
        nat_data[cc].append(float(row.customer_total or 0))

    nationality_avg = [
        {
            "country_code": cc,
            "avg_clv": round(sum(vals) / len(vals), 0) if vals else 0,
            "customer_count": len(vals),
        }
        for cc, vals in sorted(nat_data.items())
    ]

    return {
        "days": days,
        "top_n": top_n,
        "customers": customers,
        "nationality_avg": nationality_avg,
    }


@router.get("/revenue-heatmap")
async def get_revenue_heatmap(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revenue heatmap by day-of-week and hour."""
    clinic_id = current_user.clinic_id
    cutoff = date.today() - timedelta(days=days)

    result = await db.execute(
        select(
            func.extract("dow", Payment.paid_at).label("day_of_week"),
            func.extract("hour", Payment.paid_at).label("hour"),
            func.count(Payment.id).label("count"),
            func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
        )
        .where(
            Payment.clinic_id == clinic_id,
            Payment.status == "completed",
            Payment.paid_at.isnot(None),
            func.date(Payment.paid_at) >= cutoff,
        )
        .group_by(
            func.extract("dow", Payment.paid_at),
            func.extract("hour", Payment.paid_at),
        )
    )
    rows = result.all()

    heatmap = []
    for row in rows:
        heatmap.append({
            "day_of_week": int(row.day_of_week),
            "hour": int(row.hour),
            "count": row.count,
            "total_amount": float(row.total_amount),
        })

    sorted_slots = sorted(heatmap, key=lambda x: x["total_amount"], reverse=True)
    peak_slots = sorted_slots[:5]

    return {
        "days": days,
        "heatmap": heatmap,
        "peak_slots": peak_slots,
    }


# --- Churn Risk / Revisit Prediction ---


@router.get("/churn-risk")
async def get_churn_risk(
    min_risk: int = Query(default=30, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get customers sorted by churn risk score."""
    from app.services.revisit_prediction_service import RevisitPredictionService

    svc = RevisitPredictionService(db)
    customers = await svc.get_churn_risk_customers(
        clinic_id=current_user.clinic_id,
        min_risk=min_risk,
        limit=limit,
    )

    critical = sum(1 for c in customers if c["risk_level"] == "critical")
    high = sum(1 for c in customers if c["risk_level"] == "high")
    medium = sum(1 for c in customers if c["risk_level"] == "medium")

    return {
        "total_at_risk": len(customers),
        "critical_count": critical,
        "high_count": high,
        "medium_count": medium,
        "customers": [
            {
                **c,
                "customer_id": str(c["customer_id"]),
                "last_visit": str(c["last_visit"]) if c["last_visit"] else None,
            }
            for c in customers
        ],
    }


@router.get("/revisit-summary")
async def get_revisit_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get revisit prediction summary."""
    from app.services.revisit_prediction_service import RevisitPredictionService

    svc = RevisitPredictionService(db)
    return await svc.get_revisit_summary(current_user.clinic_id)
