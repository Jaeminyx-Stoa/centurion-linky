import uuid
from datetime import datetime

from pydantic import BaseModel


class TranslationReportCreate(BaseModel):
    message_id: uuid.UUID | None = None
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    corrected_text: str | None = None
    error_type: str  # wrong_term / wrong_meaning / awkward / omission / other
    severity: str  # critical / minor
    medical_term_id: uuid.UUID | None = None


class TranslationReportResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    message_id: uuid.UUID | None
    reported_by: uuid.UUID
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    corrected_text: str | None
    error_type: str
    severity: str
    medical_term_id: uuid.UUID | None
    status: str
    reviewer_id: uuid.UUID | None
    reviewer_notes: str | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TranslationReportReview(BaseModel):
    status: str  # reviewed / resolved / dismissed
    reviewer_notes: str | None = None
    corrected_text: str | None = None


class TranslationQAStats(BaseModel):
    total_reports: int
    pending_count: int
    resolved_count: int
    critical_count: int
    by_error_type: dict[str, int]
    by_language_pair: list[dict]
    accuracy_score: float | None  # percentage of messages without issues
