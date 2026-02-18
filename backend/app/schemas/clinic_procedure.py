import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ClinicProcedureCreate(BaseModel):
    procedure_id: uuid.UUID
    custom_description: str | None = None
    custom_effects: str | None = None
    custom_duration_minutes: int | None = None
    custom_effect_duration: str | None = None
    custom_downtime_days: int | None = None
    custom_min_interval_days: int | None = None
    custom_precautions_before: str | None = None
    custom_precautions_during: str | None = None
    custom_precautions_after: str | None = None
    custom_pain_level: int | None = Field(None, ge=1, le=10)
    custom_anesthesia_options: str | None = None
    material_cost: Decimal | None = None
    difficulty_score: int | None = Field(None, ge=1, le=5)
    clinic_preference: int | None = Field(None, ge=1, le=3)


class ClinicProcedureUpdate(BaseModel):
    custom_description: str | None = None
    custom_effects: str | None = None
    custom_duration_minutes: int | None = None
    custom_effect_duration: str | None = None
    custom_downtime_days: int | None = None
    custom_min_interval_days: int | None = None
    custom_precautions_before: str | None = None
    custom_precautions_during: str | None = None
    custom_precautions_after: str | None = None
    custom_pain_level: int | None = Field(None, ge=1, le=10)
    custom_anesthesia_options: str | None = None
    material_cost: Decimal | None = None
    difficulty_score: int | None = Field(None, ge=1, le=5)
    clinic_preference: int | None = Field(None, ge=1, le=3)


class ClinicProcedureResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    procedure_id: uuid.UUID
    custom_description: str | None
    custom_effects: str | None
    custom_duration_minutes: int | None
    custom_effect_duration: str | None
    custom_downtime_days: int | None
    custom_min_interval_days: int | None
    custom_precautions_before: str | None
    custom_precautions_during: str | None
    custom_precautions_after: str | None
    custom_pain_level: int | None
    custom_anesthesia_options: str | None
    material_cost: Decimal | None
    difficulty_score: int | None
    clinic_preference: int | None
    sales_performance_score: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MergedFieldValue(BaseModel):
    value: str | int | None
    source: str  # "custom" | "default"
    default_value: str | int | None


class ClinicProcedureMergedResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    procedure_id: uuid.UUID
    procedure_name_ko: str
    procedure_slug: str
    category_id: uuid.UUID | None

    # Merged fields
    description: MergedFieldValue
    effects: MergedFieldValue
    duration_minutes: MergedFieldValue
    effect_duration: MergedFieldValue
    downtime_days: MergedFieldValue
    min_interval_days: MergedFieldValue
    precautions_before: MergedFieldValue
    precautions_during: MergedFieldValue
    precautions_after: MergedFieldValue
    pain_level: MergedFieldValue
    anesthesia_options: MergedFieldValue

    # Business data
    material_cost: Decimal | None
    difficulty_score: int | None
    clinic_preference: int | None
    sales_performance_score: Decimal | None
    is_active: bool
