import uuid
from datetime import datetime

from pydantic import BaseModel


class ConversationListResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    messenger_account_id: uuid.UUID
    status: str
    ai_mode: bool
    satisfaction_score: int | None
    satisfaction_level: str | None
    last_message_at: datetime | None
    last_message_preview: str | None
    unread_count: int
    created_at: datetime
    # Joined fields
    customer_name: str | None = None
    customer_country: str | None = None
    customer_language: str | None = None
    messenger_type: str | None = None

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    messenger_account_id: uuid.UUID
    status: str
    ai_mode: bool
    assigned_to: uuid.UUID | None
    satisfaction_score: int | None
    satisfaction_level: str | None
    last_message_at: datetime | None
    last_message_preview: str | None
    unread_count: int
    summary: str | None
    detected_intents: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_type: str
    sender_id: uuid.UUID | None
    content: str
    content_type: str
    original_language: str | None
    translated_content: str | None
    translated_language: str | None
    messenger_type: str | None
    ai_metadata: dict | None
    attachments: list | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str


class CustomerDetailResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    messenger_type: str
    messenger_user_id: str
    name: str | None
    display_name: str | None
    profile_image: str | None
    country_code: str | None
    language_code: str | None
    timezone: str | None
    phone: str | None
    email: str | None
    tags: list[str] | None
    notes: str | None
    medical_conditions: dict | None = None
    allergies: dict | None = None
    medications: dict | None = None
    total_bookings: int
    last_visit_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerUpdateRequest(BaseModel):
    name: str | None = None
    display_name: str | None = None
    country_code: str | None = None
    language_code: str | None = None
    phone: str | None = None
    email: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    medical_conditions: dict | None = None
    allergies: dict | None = None
    medications: dict | None = None
