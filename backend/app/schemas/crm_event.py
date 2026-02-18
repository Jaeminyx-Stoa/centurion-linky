import uuid
from datetime import datetime

from pydantic import BaseModel


class CRMEventResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    customer_id: uuid.UUID
    payment_id: uuid.UUID | None
    booking_id: uuid.UUID | None
    event_type: str
    scheduled_at: datetime
    executed_at: datetime | None
    status: str
    message_content: str | None
    response: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
