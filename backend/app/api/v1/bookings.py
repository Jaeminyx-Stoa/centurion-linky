import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.dependencies import get_current_user
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import (
    BookingCancel,
    BookingCreate,
    BookingResponse,
    BookingUpdate,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


async def _get_booking(
    db: AsyncSession, booking_id: uuid.UUID, clinic_id: uuid.UUID
) -> Booking:
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.clinic_id == clinic_id,
        )
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


def _calc_remaining(
    total_amount: Decimal | None, deposit_amount: Decimal | None
) -> Decimal | None:
    if total_amount is not None and deposit_amount is not None:
        return total_amount - deposit_amount
    return None


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    body: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    remaining = _calc_remaining(body.total_amount, body.deposit_amount)
    booking = Booking(
        clinic_id=current_user.clinic_id,
        customer_id=body.customer_id,
        conversation_id=body.conversation_id,
        clinic_procedure_id=body.clinic_procedure_id,
        booking_date=body.booking_date,
        booking_time=body.booking_time,
        total_amount=body.total_amount,
        currency=body.currency,
        deposit_amount=body.deposit_amount,
        remaining_amount=remaining,
        notes=body.notes,
    )
    db.add(booking)
    await db.flush()
    return booking


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Booking).where(Booking.clinic_id == current_user.clinic_id)
    if status:
        stmt = stmt.where(Booking.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_booking(db, booking_id, current_user.clinic_id)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: uuid.UUID,
    body: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await _get_booking(db, booking_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    # Recalculate remaining
    booking.remaining_amount = _calc_remaining(
        booking.total_amount, booking.deposit_amount
    )
    await db.flush()
    await db.refresh(booking)
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    body: BookingCancel = BookingCancel(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await _get_booking(db, booking_id, current_user.clinic_id)
    if booking.status in ("completed", "cancelled"):
        raise BadRequestError(
            f"Cannot cancel booking with status '{booking.status}'"
        )
    booking.status = "cancelled"
    booking.cancellation_reason = body.cancellation_reason
    await db.flush()
    await db.refresh(booking)
    return booking


@router.post("/{booking_id}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await _get_booking(db, booking_id, current_user.clinic_id)
    if booking.status != "confirmed":
        raise BadRequestError(
            "Only confirmed bookings can be completed"
        )
    booking.status = "completed"
    await db.flush()
    await db.refresh(booking)
    return booking
