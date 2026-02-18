import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreateLink(BaseModel):
    booking_id: uuid.UUID | None = None
    customer_id: uuid.UUID
    payment_type: str  # deposit / remaining / full / additional
    amount: Decimal = Field(..., gt=0)
    currency: str = "KRW"
    pg_provider: str | None = None  # override auto-routing


class PaymentRequestRemaining(BaseModel):
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = "KRW"


class PaymentResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    booking_id: uuid.UUID | None
    customer_id: uuid.UUID
    payment_type: str
    amount: Decimal
    currency: str
    pg_provider: str | None
    pg_payment_id: str | None
    payment_method: str | None
    payment_link: str | None
    qr_code_url: str | None
    link_expires_at: datetime | None
    status: str
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    paid_at: datetime | None

    model_config = {"from_attributes": True}
