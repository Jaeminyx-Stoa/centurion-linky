import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AnalyticsOverviewResponse(BaseModel):
    total_conversations: int
    active_conversations: int
    resolved_conversations: int
    total_bookings: int
    total_payments: int


class ConsultationPerformanceResponse(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    period_year: int
    period_month: int
    total_score: Decimal
    sales_mix_score: Decimal
    booking_conversion_score: Decimal
    payment_conversion_score: Decimal
    booking_conversion_rate: Decimal
    payment_conversion_rate: Decimal
    total_consultations: int
    total_bookings: int
    total_payments: int
    created_at: datetime

    model_config = {"from_attributes": True}
