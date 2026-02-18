import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SettlementResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    period_year: int
    period_month: int
    total_payment_amount: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    vat_amount: Decimal
    total_settlement: Decimal
    total_payment_count: int
    status: str
    notes: str | None
    confirmed_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class SettlementGenerate(BaseModel):
    year: int
    month: int
