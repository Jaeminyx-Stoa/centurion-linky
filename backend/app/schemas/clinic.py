import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ClinicUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    email: str | None = None
    timezone: str | None = None
    logo_url: str | None = None


class ClinicSettingsUpdate(BaseModel):
    settings: dict


class ClinicResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    business_number: str | None
    phone: str | None
    email: str | None
    address: str | None
    timezone: str
    logo_url: str | None
    commission_rate: Decimal
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
