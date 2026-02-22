import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.pagination import paginate
from app.dependencies import get_current_user, get_pagination
from app.models.booking import Booking
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.models.payment import Payment
from app.models.user import User
from app.schemas.contraindication import ContraindicationCheckResponse
from app.schemas.conversation import CustomerDetailResponse, CustomerUpdateRequest
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services.contraindication_service import ContraindicationService

router = APIRouter(prefix="/customers", tags=["customers"])


async def _get_customer(
    db: AsyncSession, customer_id: uuid.UUID, clinic_id: uuid.UUID
) -> Customer:
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.clinic_id == clinic_id,
        )
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        raise NotFoundError("Customer not found")
    return customer


@router.get("")
async def list_customers(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CustomerDetailResponse]:
    stmt = (
        select(Customer)
        .where(Customer.clinic_id == current_user.clinic_id)
        .order_by(Customer.created_at.desc())
    )
    return await paginate(db, stmt, pagination)


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_customer(db, customer_id, current_user.clinic_id)


@router.patch("/{customer_id}", response_model=CustomerDetailResponse)
async def update_customer(
    customer_id: uuid.UUID,
    body: CustomerUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer = await _get_customer(db, customer_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    await db.flush()
    return customer


@router.get(
    "/{customer_id}/contraindication-check",
    response_model=ContraindicationCheckResponse,
)
async def check_contraindications(
    customer_id: uuid.UUID,
    procedure_id: uuid.UUID = Query(..., description="Clinic procedure ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_customer(db, customer_id, current_user.clinic_id)
    svc = ContraindicationService(db)
    return await svc.check(customer_id, procedure_id, current_user.clinic_id)


@router.get("/{customer_id}/history")
async def get_customer_history(
    customer_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get consolidated history for a customer: conversations, bookings, payments."""
    customer = await _get_customer(db, customer_id, current_user.clinic_id)
    clinic_id = current_user.clinic_id

    # Conversations (recent, with message count)
    conv_result = await db.execute(
        select(
            Conversation.id,
            Conversation.status,
            Conversation.ai_mode,
            Conversation.satisfaction_score,
            Conversation.last_message_at,
            Conversation.last_message_preview,
            Conversation.created_at,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(
            Conversation.customer_id == customer_id,
            Conversation.clinic_id == clinic_id,
        )
        .group_by(Conversation.id)
        .order_by(Conversation.last_message_at.desc().nulls_last())
        .limit(limit)
    )
    conversations = [
        {
            "id": str(row.id),
            "status": row.status,
            "ai_mode": row.ai_mode,
            "satisfaction_score": row.satisfaction_score,
            "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
            "last_message_preview": row.last_message_preview,
            "message_count": row.message_count,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in conv_result.all()
    ]

    # Bookings
    booking_result = await db.execute(
        select(Booking)
        .where(
            Booking.customer_id == customer_id,
            Booking.clinic_id == clinic_id,
        )
        .order_by(Booking.booking_date.desc())
        .limit(limit)
    )
    bookings = [
        {
            "id": str(b.id),
            "booking_date": b.booking_date.isoformat(),
            "booking_time": b.booking_time.isoformat(),
            "status": b.status,
            "total_amount": float(b.total_amount) if b.total_amount else None,
            "currency": b.currency,
            "notes": b.notes,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in booking_result.scalars().all()
    ]

    # Payments
    payment_result = await db.execute(
        select(Payment)
        .where(
            Payment.customer_id == customer_id,
            Payment.clinic_id == clinic_id,
        )
        .order_by(Payment.created_at.desc())
        .limit(limit)
    )
    payments = [
        {
            "id": str(p.id),
            "payment_type": p.payment_type,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "payment_method": p.payment_method,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payment_result.scalars().all()
    ]

    return {
        "customer_id": str(customer_id),
        "conversations": conversations,
        "bookings": bookings,
        "payments": payments,
        "summary": {
            "total_conversations": len(conversations),
            "total_bookings": len(bookings),
            "total_payments": len(payments),
            "total_spent": sum(p["amount"] for p in payments if p["status"] == "completed"),
        },
    }
