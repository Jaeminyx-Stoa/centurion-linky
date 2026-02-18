import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MessengerAccountCreate(BaseModel):
    messenger_type: str = Field(..., pattern=r"^(telegram|instagram|facebook|whatsapp|line|kakao)$")
    account_name: str = Field(..., min_length=1, max_length=200)
    display_name: str | None = None
    credentials: dict
    target_countries: list[str] | None = None


class MessengerAccountUpdate(BaseModel):
    account_name: str | None = None
    display_name: str | None = None
    credentials: dict | None = None
    target_countries: list[str] | None = None
    is_active: bool | None = None


class MessengerAccountResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    messenger_type: str
    account_name: str
    display_name: str | None
    webhook_url: str | None
    target_countries: list[str] | None
    is_active: bool
    is_connected: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
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
