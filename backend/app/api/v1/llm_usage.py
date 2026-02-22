"""LLM usage cost tracking API — monthly summary, daily trend, and quota management."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.clinic import Clinic
from app.models.llm_usage import LLMUsage
from app.models.user import User

router = APIRouter(prefix="/llm-usage", tags=["llm-usage"])


@router.get("/summary")
async def get_monthly_summary(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Monthly LLM usage summary grouped by operation."""
    clinic_id = current_user.clinic_id
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    result = await db.execute(
        select(
            LLMUsage.operation,
            func.count(LLMUsage.id).label("count"),
            func.sum(LLMUsage.input_tokens).label("input_tokens"),
            func.sum(LLMUsage.output_tokens).label("output_tokens"),
            func.sum(LLMUsage.total_tokens).label("total_tokens"),
            func.sum(LLMUsage.cost_usd).label("cost_usd"),
        )
        .where(
            LLMUsage.clinic_id == clinic_id,
            func.date(LLMUsage.created_at) >= start_date,
            func.date(LLMUsage.created_at) < end_date,
        )
        .group_by(LLMUsage.operation)
    )
    rows = result.all()

    items = []
    total_cost = 0.0
    total_tokens_all = 0
    for row in rows:
        cost = float(row.cost_usd or 0)
        tokens = int(row.total_tokens or 0)
        total_cost += cost
        total_tokens_all += tokens
        items.append({
            "operation": row.operation,
            "count": row.count,
            "input_tokens": int(row.input_tokens or 0),
            "output_tokens": int(row.output_tokens or 0),
            "total_tokens": tokens,
            "cost_usd": round(cost, 6),
        })

    return {
        "year": year,
        "month": month,
        "clinic_id": str(clinic_id),
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens_all,
        "by_operation": items,
    }


@router.get("/daily")
async def get_daily_trend(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Daily LLM cost trend for the last N days."""
    clinic_id = current_user.clinic_id
    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(LLMUsage.created_at).label("day"),
            func.count(LLMUsage.id).label("count"),
            func.sum(LLMUsage.total_tokens).label("total_tokens"),
            func.sum(LLMUsage.cost_usd).label("cost_usd"),
        )
        .where(
            LLMUsage.clinic_id == clinic_id,
            func.date(LLMUsage.created_at) >= start_date,
        )
        .group_by(func.date(LLMUsage.created_at))
        .order_by(func.date(LLMUsage.created_at))
    )
    rows = result.all()

    return {
        "clinic_id": str(clinic_id),
        "days": days,
        "data": [
            {
                "date": str(row.day),
                "count": row.count,
                "total_tokens": int(row.total_tokens or 0),
                "cost_usd": round(float(row.cost_usd or 0), 6),
            }
            for row in rows
        ],
    }


class QuotaUpdateRequest(BaseModel):
    monthly_quota_usd: float


@router.get("/quota")
async def get_quota(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current LLM quota and this month's usage."""
    clinic_id = current_user.clinic_id

    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one()

    # Current month cost
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    cost_result = await db.execute(
        select(func.coalesce(func.sum(LLMUsage.cost_usd), 0.0)).where(
            LLMUsage.clinic_id == clinic_id,
            func.date(LLMUsage.created_at) >= start_of_month,
        )
    )
    monthly_cost = float(cost_result.scalar() or 0.0)

    quota = clinic.llm_monthly_quota_usd
    return {
        "clinic_id": str(clinic_id),
        "monthly_quota_usd": quota,
        "current_month_cost_usd": round(monthly_cost, 6),
        "usage_percent": round(monthly_cost / quota * 100, 1) if quota and quota > 0 else None,
        "alert_sent": clinic.llm_quota_alert_sent,
    }


@router.patch("/quota")
async def update_quota(
    body: QuotaUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set the monthly LLM cost quota for the clinic."""
    clinic_id = current_user.clinic_id

    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one()

    clinic.llm_monthly_quota_usd = body.monthly_quota_usd
    # Reset alert flag when quota changes
    clinic.llm_quota_alert_sent = False
    await db.flush()

    return {
        "clinic_id": str(clinic_id),
        "monthly_quota_usd": clinic.llm_monthly_quota_usd,
    }
