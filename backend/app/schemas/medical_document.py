import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChartDraftContent(BaseModel):
    chief_complaint: str | None = None
    desired_procedures: list[str] = []
    medical_history: str | None = None
    allergies: str | None = None
    medications: str | None = None
    skin_type: str | None = None
    ai_recommendations: str | None = None
    notes: str | None = None


class ConsentFormContent(BaseModel):
    procedure_name: str
    procedure_description: str | None = None
    risks: list[str] = []
    alternatives: str | None = None
    expected_results: str | None = None
    aftercare_instructions: str | None = None
    patient_acknowledgements: list[str] = []


class MedicalDocumentCreate(BaseModel):
    customer_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    document_type: str = Field(..., pattern="^(chart_draft|consent_form)$")
    title: str = Field(..., max_length=200)
    content: dict | None = None
    language: str = "ko"


class MedicalDocumentResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str | None = None
    booking_id: uuid.UUID | None
    conversation_id: uuid.UUID | None
    document_type: str
    title: str
    content: dict | None
    language: str
    status: str
    generated_by: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentGenerateRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    booking_id: uuid.UUID | None = None
    language: str = "ko"


class DocumentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|reviewed|signed|archived)$")
