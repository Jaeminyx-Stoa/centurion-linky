import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AIPersonaCreate(BaseModel):
    name: str = Field(..., max_length=100)
    personality: str | None = None
    system_prompt: str | None = None
    avatar_url: str | None = None
    is_default: bool = False


class AIPersonaUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    personality: str | None = None
    system_prompt: str | None = None
    avatar_url: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class AIPersonaResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    personality: str | None
    system_prompt: str | None
    avatar_url: str | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
