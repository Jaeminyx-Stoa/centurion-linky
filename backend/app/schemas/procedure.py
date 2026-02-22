import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProcedureCreate(BaseModel):
    category_id: uuid.UUID | None = None
    name_ko: str = Field(..., min_length=1, max_length=200)
    name_en: str | None = None
    name_ja: str | None = None
    name_zh: str | None = None
    name_vi: str | None = None
    slug: str = Field(..., min_length=1, max_length=200, pattern=r"^[a-z0-9\-]+$")
    description_ko: str | None = None
    description_en: str | None = None
    effects_ko: str | None = None
    duration_minutes: int | None = None
    effect_duration: str | None = None
    downtime_days: int | None = None
    min_interval_days: int | None = None
    common_side_effects: str | None = None
    rare_side_effects: str | None = None
    dangerous_side_effects: str | None = None
    precautions_before: str | None = None
    precautions_during: str | None = None
    precautions_after: str | None = None
    pain_level: int | None = Field(None, ge=1, le=10)
    pain_type: str | None = None
    anesthesia_options: str | None = None
    anesthesia_details: dict | None = None
    contraindications: dict | None = None


class ProcedureUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    name_ko: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = None
    name_ja: str | None = None
    name_zh: str | None = None
    name_vi: str | None = None
    description_ko: str | None = None
    description_en: str | None = None
    effects_ko: str | None = None
    duration_minutes: int | None = None
    effect_duration: str | None = None
    downtime_days: int | None = None
    min_interval_days: int | None = None
    common_side_effects: str | None = None
    rare_side_effects: str | None = None
    dangerous_side_effects: str | None = None
    precautions_before: str | None = None
    precautions_during: str | None = None
    precautions_after: str | None = None
    pain_level: int | None = Field(None, ge=1, le=10)
    pain_type: str | None = None
    anesthesia_options: str | None = None
    anesthesia_details: dict | None = None
    contraindications: dict | None = None
    is_active: bool | None = None


class ProcedureResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID | None
    name_ko: str
    name_en: str | None
    name_ja: str | None
    name_zh: str | None
    name_vi: str | None
    slug: str
    description_ko: str | None
    description_en: str | None
    effects_ko: str | None
    duration_minutes: int | None
    effect_duration: str | None
    downtime_days: int | None
    min_interval_days: int | None
    common_side_effects: str | None
    rare_side_effects: str | None
    dangerous_side_effects: str | None
    precautions_before: str | None
    precautions_during: str | None
    precautions_after: str | None
    pain_level: int | None
    pain_type: str | None
    anesthesia_options: str | None
    anesthesia_details: dict | None
    contraindications: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
