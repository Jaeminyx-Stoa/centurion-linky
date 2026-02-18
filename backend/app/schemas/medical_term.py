import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MedicalTermCreate(BaseModel):
    term_ko: str = Field(..., min_length=1, max_length=200)
    translations: dict = Field(default_factory=dict)
    category: str = Field(..., pattern=r"^(procedure|symptom|body_part|material|general)$")
    description: str | None = None


class MedicalTermUpdate(BaseModel):
    term_ko: str | None = None
    translations: dict | None = None
    category: str | None = Field(None, pattern=r"^(procedure|symptom|body_part|material|general)$")
    description: str | None = None
    is_verified: bool | None = None
    is_active: bool | None = None


class MedicalTermResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID | None
    term_ko: str
    translations: dict
    category: str
    description: str | None
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
