from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PaymentLinkResult:
    link: str
    qr_url: str | None
    provider_payment_id: str
    expires_at: datetime | None = None


@dataclass
class PaymentResult:
    provider_payment_id: str
    status: str  # completed / failed / pending
    amount: float
    currency: str
    payment_method: str | None = None
    paid_at: datetime | None = None
    raw_data: dict = field(default_factory=dict)


@dataclass
class RefundResult:
    provider_refund_id: str
    status: str  # completed / pending / failed
    amount: float
    raw_data: dict = field(default_factory=dict)


class AbstractPaymentProvider(ABC):
    """Base interface for all payment provider adapters."""

    @abstractmethod
    async def create_payment_link(
        self, amount: float, currency: str, metadata: dict | None = None
    ) -> PaymentLinkResult:
        """Create a payment link and optional QR code URL."""

    @abstractmethod
    async def verify_webhook(
        self, request_data: bytes, headers: dict
    ) -> bool:
        """Verify webhook request authenticity."""

    @abstractmethod
    async def parse_webhook(self, request_data: dict) -> PaymentResult:
        """Parse webhook payload into PaymentResult."""

    @abstractmethod
    async def get_payment_status(self, provider_payment_id: str) -> str:
        """Get current payment status from provider."""

    @abstractmethod
    async def refund(
        self, provider_payment_id: str, amount: float | None = None
    ) -> RefundResult:
        """Request a refund."""
