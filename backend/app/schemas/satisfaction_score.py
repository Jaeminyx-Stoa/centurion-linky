import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SatisfactionScoreResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    clinic_id: uuid.UUID
    score: int
    level: str
    language_signals: dict | None
    behavior_signals: dict | None
    flow_signals: dict | None
    supervisor_override: int | None
    supervisor_note: str | None
    supervised_by: uuid.UUID | None
    supervised_at: datetime | None
    alert_sent: bool
    alert_sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SupervisorOverride(BaseModel):
    corrected_score: int = Field(..., ge=0, le=100)
    note: str | None = None
