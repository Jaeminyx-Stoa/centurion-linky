import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FollowupRuleCreate(BaseModel):
    procedure_id: uuid.UUID | None = None
    event_type: str = Field(..., max_length=30)
    delay_days: int = Field(..., ge=0)
    delay_hours: int = Field(0, ge=0, le=23)
    message_template: dict | None = None
    sort_order: int = 0
    is_active: bool = True


class FollowupRuleUpdate(BaseModel):
    procedure_id: uuid.UUID | None = None
    event_type: str | None = Field(None, max_length=30)
    delay_days: int | None = Field(None, ge=0)
    delay_hours: int | None = Field(None, ge=0, le=23)
    message_template: dict | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class FollowupRuleResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    procedure_id: uuid.UUID | None
    procedure_name: str | None = None
    event_type: str
    delay_days: int
    delay_hours: int
    message_template: dict | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SideEffectKeywordCreate(BaseModel):
    language: str = Field(..., max_length=5)
    keywords: list[str]
    severity: str = Field("normal", pattern="^(urgent|normal)$")


class SideEffectKeywordResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    language: str
    keywords: list[str]
    severity: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SideEffectAlertResponse(BaseModel):
    customer_id: uuid.UUID
    customer_name: str | None = None
    conversation_id: uuid.UUID
    matched_keywords: list[str]
    severity: str
    message_preview: str
    detected_at: datetime
