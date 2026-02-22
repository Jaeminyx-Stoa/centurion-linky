import uuid
from datetime import datetime

from pydantic import BaseModel


class TreatmentPhotoCreate(BaseModel):
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    procedure_id: uuid.UUID | None = None
    photo_type: str  # before / after / progress
    description: str | None = None
    taken_at: datetime | None = None
    days_after_procedure: int | None = None
    is_consent_given: bool = False
    pair_id: uuid.UUID | None = None


class TreatmentPhotoResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None
    procedure_id: uuid.UUID | None
    photo_type: str
    photo_url: str
    thumbnail_url: str | None
    description: str | None
    taken_at: datetime | None
    days_after_procedure: int | None
    is_consent_given: bool
    is_portfolio_approved: bool
    approved_by: uuid.UUID | None
    pair_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TreatmentPhotoUpdate(BaseModel):
    description: str | None = None
    is_consent_given: bool | None = None
    is_portfolio_approved: bool | None = None
    days_after_procedure: int | None = None


class PhotoPairResponse(BaseModel):
    pair_id: uuid.UUID
    before: TreatmentPhotoResponse | None
    after: TreatmentPhotoResponse | None
    procedure_name: str | None
    customer_name: str | None
