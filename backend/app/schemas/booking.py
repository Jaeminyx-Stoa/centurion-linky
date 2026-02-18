import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    customer_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    clinic_procedure_id: uuid.UUID | None = None
    booking_date: date
    booking_time: time
    total_amount: Decimal | None = Field(None, ge=0)
    currency: str = "KRW"
    deposit_amount: Decimal | None = Field(None, ge=0)
    notes: str | None = None


class BookingUpdate(BaseModel):
    booking_date: date | None = None
    booking_time: time | None = None
    total_amount: Decimal | None = Field(None, ge=0)
    currency: str | None = None
    deposit_amount: Decimal | None = Field(None, ge=0)
    notes: str | None = None


class BookingResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    conversation_id: uuid.UUID | None
    clinic_procedure_id: uuid.UUID | None
    booking_date: date
    booking_time: time
    status: str
    total_amount: Decimal | None
    currency: str
    deposit_amount: Decimal | None
    remaining_amount: Decimal | None
    notes: str | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingCancel(BaseModel):
    cancellation_reason: str | None = None
