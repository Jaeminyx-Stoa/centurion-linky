import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.procedure_pricing import ProcedurePricing
from app.models.user import User
from app.schemas.procedure_pricing import (
    ProcedurePricingCreate,
    ProcedurePricingResponse,
    ProcedurePricingUpdate,
)
from app.services.pricing_service import calculate_discount

router = APIRouter(prefix="/pricing", tags=["pricing"])


async def _get_pricing(
    db: AsyncSession, pricing_id: uuid.UUID, clinic_id: uuid.UUID
) -> ProcedurePricing:
    result = await db.execute(
        select(ProcedurePricing).where(
            ProcedurePricing.id == pricing_id,
            ProcedurePricing.clinic_id == clinic_id,
        )
    )
    pricing = result.scalar_one_or_none()
    if pricing is None:
        raise NotFoundError("Pricing not found")
    return pricing


@router.post("", response_model=ProcedurePricingResponse, status_code=201)
async def create_pricing(
    body: ProcedurePricingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    discount_rate, discount_warning = calculate_discount(
        body.regular_price, body.event_price
    )
    pricing = ProcedurePricing(
        clinic_id=current_user.clinic_id,
        clinic_procedure_id=body.clinic_procedure_id,
        regular_price=body.regular_price,
        event_price=body.event_price,
        discount_rate=discount_rate,
        discount_warning=discount_warning,
        event_start_date=body.event_start_date,
        event_end_date=body.event_end_date,
        is_package=body.is_package,
        package_details=body.package_details,
        prices_by_currency=body.prices_by_currency,
    )
    db.add(pricing)
    await db.flush()
    return pricing


@router.get("", response_model=list[ProcedurePricingResponse])
async def list_pricing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcedurePricing).where(
            ProcedurePricing.clinic_id == current_user.clinic_id,
            ProcedurePricing.is_active.is_(True),
        )
    )
    return result.scalars().all()


@router.patch("/{pricing_id}", response_model=ProcedurePricingResponse)
async def update_pricing(
    pricing_id: uuid.UUID,
    body: ProcedurePricingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pricing = await _get_pricing(db, pricing_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pricing, field, value)

    # Recalculate discount
    discount_rate, discount_warning = calculate_discount(
        pricing.regular_price, pricing.event_price
    )
    pricing.discount_rate = discount_rate
    pricing.discount_warning = discount_warning

    await db.flush()
    await db.refresh(pricing)
    return pricing


@router.delete("/{pricing_id}", status_code=204)
async def delete_pricing(
    pricing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pricing = await _get_pricing(db, pricing_id, current_user.clinic_id)
    pricing.is_active = False
    await db.flush()
