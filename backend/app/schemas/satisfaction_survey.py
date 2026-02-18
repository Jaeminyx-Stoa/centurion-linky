import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SatisfactionSurveyCreate(BaseModel):
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    crm_event_id: uuid.UUID | None = None
    survey_round: int = Field(..., ge=1, le=3)
    satisfaction_score: int | None = Field(None, ge=1, le=5)
    revisit_intention: str | None = None  # yes / maybe / no
    nps_score: int | None = Field(None, ge=0, le=10)
    feedback_text: str | None = None
    side_effects_reported: str | None = None


class SatisfactionSurveyResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None
    crm_event_id: uuid.UUID | None
    survey_round: int
    satisfaction_score: int | None
    revisit_intention: str | None
    nps_score: int | None
    feedback_text: str | None
    side_effects_reported: str | None
    responded_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SurveySummaryResponse(BaseModel):
    total_surveys: int
    avg_satisfaction: float | None
    avg_nps: float | None
    revisit_yes_pct: float | None
    by_round: dict  # {1: {count, avg_score}, 2: {...}, 3: {...}}

    model_config = {"from_attributes": True}


class CRMDashboardResponse(BaseModel):
    total_events: int
    scheduled: int
    sent: int
    completed: int
    cancelled: int
    failed: int
    total_surveys: int
    avg_satisfaction: float | None
    avg_nps: float | None
