"""Platform admin API — superadmin-only endpoints for managing clinics and viewing platform metrics."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.pagination import paginate
from app.dependencies import get_pagination, require_role
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.payment import Payment
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.settlement import SettlementResponse

router = APIRouter(prefix="/admin", tags=["admin"])

superadmin = require_role("superadmin")


# --- Schemas ---

class AdminClinicResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    commission_rate: float
    user_count: int = 0
    conversation_count: int = 0

    model_config = {"from_attributes": True}


class AdminClinicUpdate(BaseModel):
    is_active: bool | None = None
    commission_rate: float | None = None


class PlatformAnalyticsResponse(BaseModel):
    total_clinics: int
    active_clinics: int
    total_conversations: int
    total_users: int
    total_revenue: float


# --- Endpoints ---

@router.get("/clinics")
async def list_clinics(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(superadmin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AdminClinicResponse]:
    """List all clinics with user and conversation counts."""
    # Count total
    count_result = await db.execute(select(func.count(Clinic.id)))
    total = count_result.scalar() or 0

    # Fetch clinics
    result = await db.execute(
        select(Clinic)
        .order_by(Clinic.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    clinics = result.scalars().all()

    items = []
    for c in clinics:
        # Subquery counts
        user_count = (await db.execute(
            select(func.count(User.id)).where(User.clinic_id == c.id)
        )).scalar() or 0

        conv_count = (await db.execute(
            select(func.count(Conversation.id)).where(Conversation.clinic_id == c.id)
        )).scalar() or 0

        items.append(AdminClinicResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            is_active=c.is_active,
            commission_rate=float(c.commission_rate),
            user_count=user_count,
            conversation_count=conv_count,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/clinics/{clinic_id}", response_model=AdminClinicResponse)
async def get_clinic(
    clinic_id: uuid.UUID,
    current_user: User = Depends(superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single clinic's details."""
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()
    if clinic is None:
        raise NotFoundError("Clinic not found")

    user_count = (await db.execute(
        select(func.count(User.id)).where(User.clinic_id == clinic_id)
    )).scalar() or 0

    conv_count = (await db.execute(
        select(func.count(Conversation.id)).where(Conversation.clinic_id == clinic_id)
    )).scalar() or 0

    return AdminClinicResponse(
        id=clinic.id,
        name=clinic.name,
        slug=clinic.slug,
        is_active=clinic.is_active,
        commission_rate=float(clinic.commission_rate),
        user_count=user_count,
        conversation_count=conv_count,
    )


@router.patch("/clinics/{clinic_id}", response_model=AdminClinicResponse)
async def update_clinic(
    clinic_id: uuid.UUID,
    body: AdminClinicUpdate,
    current_user: User = Depends(superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Update clinic settings (is_active, commission_rate)."""
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()
    if clinic is None:
        raise NotFoundError("Clinic not found")

    if body.is_active is not None:
        clinic.is_active = body.is_active
    if body.commission_rate is not None:
        from decimal import Decimal
        clinic.commission_rate = Decimal(str(body.commission_rate))

    await db.flush()
    await db.refresh(clinic)

    return AdminClinicResponse(
        id=clinic.id,
        name=clinic.name,
        slug=clinic.slug,
        is_active=clinic.is_active,
        commission_rate=float(clinic.commission_rate),
    )


@router.get("/settlements")
async def list_all_settlements(
    year: int | None = Query(None),
    month: int | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(superadmin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SettlementResponse]:
    """List all settlements across all clinics (no clinic filter)."""
    stmt = select(Settlement)
    if year is not None:
        stmt = stmt.where(Settlement.period_year == year)
    if month is not None:
        stmt = stmt.where(Settlement.period_month == month)
    stmt = stmt.order_by(
        Settlement.period_year.desc(), Settlement.period_month.desc()
    )
    return await paginate(db, stmt, pagination)


@router.get("/analytics/platform", response_model=PlatformAnalyticsResponse)
async def platform_analytics(
    current_user: User = Depends(superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide analytics summary."""
    total_clinics = (await db.execute(
        select(func.count(Clinic.id))
    )).scalar() or 0

    active_clinics = (await db.execute(
        select(func.count(Clinic.id)).where(Clinic.is_active.is_(True))
    )).scalar() or 0

    total_conversations = (await db.execute(
        select(func.count(Conversation.id))
    )).scalar() or 0

    total_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active.is_(True))
    )).scalar() or 0

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "completed"
        )
    )
    total_revenue = float(revenue_result.scalar() or 0)

    return PlatformAnalyticsResponse(
        total_clinics=total_clinics,
        active_clinics=active_clinics,
        total_conversations=total_conversations,
        total_users=total_users,
        total_revenue=total_revenue,
    )
