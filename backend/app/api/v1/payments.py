import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import (
    PaymentCreateLink,
    PaymentRequestRemaining,
    PaymentResponse,
    PaymentStatusResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


async def _get_payment(
    db: AsyncSession, payment_id: uuid.UUID, clinic_id: uuid.UUID
) -> Payment:
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.clinic_id == clinic_id,
        )
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Payment not found")
    return payment


@router.post("/create-link", response_model=PaymentResponse, status_code=201)
async def create_payment_link(
    body: PaymentCreateLink,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PaymentService(db)
    payment = await service.create_payment_link(
        clinic_id=current_user.clinic_id,
        booking_id=body.booking_id,
        customer_id=body.customer_id,
        payment_type=body.payment_type,
        amount=float(body.amount),
        currency=body.currency,
        provider_type=body.pg_provider,
    )
    return payment


@router.post("/request-remaining", response_model=PaymentResponse, status_code=201)
async def request_remaining(
    body: PaymentRequestRemaining,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PaymentService(db)
    payment = await service.request_remaining(
        clinic_id=current_user.clinic_id,
        booking_id=body.booking_id,
        customer_id=body.customer_id,
        amount=float(body.amount),
        currency=body.currency,
    )
    return payment


@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    booking_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payment).where(Payment.clinic_id == current_user.clinic_id)
    if booking_id:
        stmt = stmt.where(Payment.booking_id == booking_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_payment(db, payment_id, current_user.clinic_id)


@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_payment(db, payment_id, current_user.clinic_id)
