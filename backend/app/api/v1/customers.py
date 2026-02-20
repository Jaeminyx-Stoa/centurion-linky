import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.pagination import paginate
from app.dependencies import get_current_user, get_pagination
from app.models.customer import Customer
from app.models.user import User
from app.schemas.conversation import CustomerDetailResponse, CustomerUpdateRequest
from app.schemas.pagination import PaginatedResponse, PaginationParams

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
