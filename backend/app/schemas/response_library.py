import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ResponseLibraryCreate(BaseModel):
    category: str = Field(
        ..., pattern=r"^(pricing|procedure|booking|aftercare|general)$"
    )
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    subcategory: str | None = None
    language_code: str = "ko"
    tags: list[str] | None = None


class ResponseLibraryUpdate(BaseModel):
    category: str | None = Field(
        None, pattern=r"^(pricing|procedure|booking|aftercare|general)$"
    )
    question: str | None = None
    answer: str | None = None
    subcategory: str | None = None
    language_code: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class ResponseLibraryResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    category: str
    subcategory: str | None
    question: str
    answer: str
    language_code: str
    tags: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
