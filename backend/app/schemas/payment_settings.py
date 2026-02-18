from pydantic import BaseModel


class PaymentSettingsResponse(BaseModel):
    default_provider: str | None = None
    default_currency: str | None = None
    deposit_required: bool | None = None
    deposit_percentage: float | None = None
    payment_expiry_hours: int | None = None

    model_config = {"from_attributes": True}


class PaymentSettingsUpdate(BaseModel):
    default_provider: str | None = None
    default_currency: str | None = None
    deposit_required: bool | None = None
    deposit_percentage: float | None = None
    payment_expiry_hours: int | None = None
