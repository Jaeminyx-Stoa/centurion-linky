import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PackageItemSchema(BaseModel):
    clinic_procedure_id: uuid.UUID
    sessions: int = Field(ge=1, default=1)
    interval_days: int = Field(ge=0, default=14)


class ProcedurePackageCreate(BaseModel):
    name_ko: str = Field(..., min_length=1, max_length=200)
    name_en: str | None = None
    name_ja: str | None = None
    name_zh: str | None = None
    name_vi: str | None = None
    description: str | None = None
    items: list[PackageItemSchema] = []
    total_sessions: int = Field(ge=1, default=1)
    package_price: Decimal | None = None
    discount_rate: Decimal | None = None


class ProcedurePackageUpdate(BaseModel):
    name_ko: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = None
    name_ja: str | None = None
    name_zh: str | None = None
    name_vi: str | None = None
    description: str | None = None
    items: list[PackageItemSchema] | None = None
    total_sessions: int | None = None
    package_price: Decimal | None = None
    discount_rate: Decimal | None = None
    is_active: bool | None = None


class ProcedurePackageResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name_ko: str
    name_en: str | None
    name_ja: str | None
    name_zh: str | None
    name_vi: str | None
    description: str | None
    items: dict | None
    total_sessions: int
    package_price: Decimal | None
    discount_rate: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PackageEnrollmentCreate(BaseModel):
    customer_id: uuid.UUID


class PackageSessionResponse(BaseModel):
    id: uuid.UUID
    enrollment_id: uuid.UUID
    session_number: int
    clinic_procedure_id: uuid.UUID | None
    booking_id: uuid.UUID | None
    status: str
    scheduled_date: date | None
    completed_at: datetime | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PackageEnrollmentResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    package_id: uuid.UUID
    status: str
    purchased_at: datetime | None
    sessions_completed: int
    next_session_date: date | None
    notes: str | None
    sessions: list[PackageSessionResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
