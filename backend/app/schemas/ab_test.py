import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ABTestVariantCreate(BaseModel):
    name: str = Field(..., max_length=100)
    config: dict = Field(default_factory=dict)
    weight: int = 50


class ABTestCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = None
    test_type: str = Field(..., max_length=50)
    variants: list[ABTestVariantCreate] = Field(..., min_length=2)


class ABTestUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    is_active: bool | None = None
    status: str | None = None


class ABTestVariantResponse(BaseModel):
    id: uuid.UUID
    ab_test_id: uuid.UUID
    name: str
    config: dict
    weight: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ABTestResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    description: str | None
    test_type: str
    status: str
    is_active: bool
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    variants: list[ABTestVariantResponse] = []

    model_config = {"from_attributes": True}


class ABTestResultCreate(BaseModel):
    variant_id: uuid.UUID
    conversation_id: uuid.UUID
    outcome: str = Field(..., max_length=50)
    outcome_data: dict | None = None


class ABTestResultResponse(BaseModel):
    id: uuid.UUID
    ab_test_id: uuid.UUID
    variant_id: uuid.UUID
    conversation_id: uuid.UUID
    outcome: str
    outcome_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ABTestStatsResponse(BaseModel):
    variant_id: str
    variant_name: str
    total_conversations: int
    positive_outcomes: int
    conversion_rate: float
