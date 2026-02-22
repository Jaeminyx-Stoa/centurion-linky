import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChecklistItemSchema(BaseModel):
    id: str
    question_ko: str
    question_en: str | None = None
    question_ja: str | None = None
    question_zh: str | None = None
    question_vi: str | None = None
    required: bool = True
    type: str = "boolean"  # boolean, text, choice
    choices: list[str] | None = None


class ConsultationProtocolCreate(BaseModel):
    procedure_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=200)
    checklist_items: list[ChecklistItemSchema] = []


class ConsultationProtocolUpdate(BaseModel):
    procedure_id: uuid.UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    checklist_items: list[ChecklistItemSchema] | None = None
    is_active: bool | None = None


class ConsultationProtocolResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    procedure_id: uuid.UUID | None
    name: str
    checklist_items: list | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProtocolStateItemResponse(BaseModel):
    id: str
    answered: bool
    answer: str | None = None


class ProtocolStateResponse(BaseModel):
    protocol_id: uuid.UUID
    total_items: int
    completed_items: int
    is_complete: bool
    items: list[ProtocolStateItemResponse]
