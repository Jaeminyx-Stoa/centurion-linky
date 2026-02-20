import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.pagination import paginate
from app.dependencies import get_current_user, get_pagination
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.settlement import SettlementGenerate, SettlementResponse
from app.services.settlement_service import SettlementService

router = APIRouter(prefix="/settlements", tags=["settlements"])


async def _get_settlement(
    db: AsyncSession, settlement_id: uuid.UUID, clinic_id: uuid.UUID
) -> Settlement:
    result = await db.execute(
        select(Settlement).where(
            Settlement.id == settlement_id,
            Settlement.clinic_id == clinic_id,
        )
    )
    settlement = result.scalar_one_or_none()
    if settlement is None:
        raise NotFoundError("Settlement not found")
    return settlement


@router.post("/generate", response_model=SettlementResponse, status_code=201)
async def generate_settlement(
    body: SettlementGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate monthly settlement for the current clinic."""
    service = SettlementService(db)
    settlement = await service.generate_monthly_settlement(
        current_user.clinic_id, body.year, body.month
    )
    return settlement


@router.get("")
async def list_settlements(
    year: int | None = Query(None),
    month: int | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SettlementResponse]:
    """List settlements for the current clinic."""
    stmt = select(Settlement).where(
        Settlement.clinic_id == current_user.clinic_id
    )
    if year is not None:
        stmt = stmt.where(Settlement.period_year == year)
    if month is not None:
        stmt = stmt.where(Settlement.period_month == month)
    stmt = stmt.order_by(
        Settlement.period_year.desc(), Settlement.period_month.desc()
    )
    return await paginate(db, stmt, pagination)


@router.get("/{settlement_id}", response_model=SettlementResponse)
async def get_settlement(
    settlement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_settlement(db, settlement_id, current_user.clinic_id)


@router.patch("/{settlement_id}/confirm", response_model=SettlementResponse)
async def confirm_settlement(
    settlement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a pending settlement."""
    settlement = await _get_settlement(
        db, settlement_id, current_user.clinic_id
    )
    if settlement.status != "pending":
        from app.core.exceptions import BadRequestError

        raise BadRequestError(
            f"Cannot confirm settlement in '{settlement.status}' status"
        )
    settlement.status = "confirmed"
    settlement.confirmed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(settlement)
    return settlement


@router.patch("/{settlement_id}/mark-paid", response_model=SettlementResponse)
async def mark_paid(
    settlement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a confirmed settlement as paid."""
    settlement = await _get_settlement(
        db, settlement_id, current_user.clinic_id
    )
    if settlement.status != "confirmed":
        from app.core.exceptions import BadRequestError

        raise BadRequestError(
            f"Cannot mark as paid settlement in '{settlement.status}' status"
        )
    settlement.status = "paid"
    settlement.paid_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(settlement)
    return settlement
