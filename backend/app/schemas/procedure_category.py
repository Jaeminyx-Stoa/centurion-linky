import uuid

from pydantic import BaseModel, Field


class ProcedureCategoryCreate(BaseModel):
    name_ko: str = Field(..., min_length=1, max_length=100)
    name_en: str | None = None
    name_ja: str | None = None
    name_zh: str | None = None
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    parent_id: uuid.UUID | None = None
    sort_order: int = 0


class ProcedureCategoryUpdate(BaseModel):
    name_ko: str | None = Field(None, min_length=1, max_length=100)
    name_en: str | None = None
    name_ja: str | None = None
    name_zh: str | None = None
    sort_order: int | None = None


class ProcedureCategoryResponse(BaseModel):
    id: uuid.UUID
    name_ko: str
    name_en: str | None
    name_ja: str | None
    name_zh: str | None
    slug: str
    parent_id: uuid.UUID | None
    sort_order: int

    model_config = {"from_attributes": True}


class ProcedureCategoryTreeResponse(ProcedureCategoryResponse):
    children: list["ProcedureCategoryTreeResponse"] = []
