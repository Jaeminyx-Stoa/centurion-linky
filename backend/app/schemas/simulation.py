import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SimulationSessionCreate(BaseModel):
    persona_name: str = Field(..., max_length=100)
    persona_config: dict = Field(default_factory=dict)
    max_rounds: int = 20


class SimulationResultResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    clinic_id: uuid.UUID
    booked: bool
    paid: bool
    escalated: bool
    abandoned: bool
    satisfaction_score: int | None
    response_quality_score: int | None
    exit_reason: str | None
    strategies_used: list | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationSessionResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    persona_name: str
    persona_config: dict
    max_rounds: int
    actual_rounds: int
    status: str
    messages: list | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    result: SimulationResultResponse | None = None

    model_config = {"from_attributes": True}


class PersonaResponse(BaseModel):
    name: str
    profile: str
    behavior: str
    language: str
    country: str
