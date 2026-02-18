import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProcedurePricingCreate(BaseModel):
    clinic_procedure_id: uuid.UUID
    regular_price: Decimal = Field(..., gt=0)
    event_price: Decimal | None = Field(None, gt=0)
    event_start_date: date | None = None
    event_end_date: date | None = None
    is_package: bool = False
    package_details: dict | None = None
    prices_by_currency: dict = Field(default_factory=dict)


class ProcedurePricingUpdate(BaseModel):
    regular_price: Decimal | None = Field(None, gt=0)
    event_price: Decimal | None = Field(None, gt=0)
    event_start_date: date | None = None
    event_end_date: date | None = None
    is_package: bool | None = None
    package_details: dict | None = None
    prices_by_currency: dict | None = None


class ProcedurePricingResponse(BaseModel):
    id: uuid.UUID
    clinic_procedure_id: uuid.UUID
    clinic_id: uuid.UUID
    regular_price: Decimal
    event_price: Decimal | None
    discount_rate: Decimal | None
    event_start_date: date | None
    event_end_date: date | None
    is_package: bool
    package_details: dict | None
    prices_by_currency: dict
    discount_warning: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
