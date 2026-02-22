"""KingOrder payment provider — Korean PG with HMAC-SHA256 webhook verification."""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone

from app.config import settings
from app.payment.base import (
    AbstractPaymentProvider,
    PaymentLinkResult,
    PaymentResult,
    RefundResult,
)

logger = logging.getLogger(__name__)


class KingOrderProvider(AbstractPaymentProvider):
    """KingOrder payment provider with QR code support."""

    async def create_payment_link(
        self, amount: float, currency: str, metadata: dict | None = None
    ) -> PaymentLinkResult:
        payment_id = f"ko_{uuid.uuid4().hex[:12]}"
        return PaymentLinkResult(
            link=f"https://pay.kingorder.kr/{payment_id}",
            qr_url=f"https://pay.kingorder.kr/qr/{payment_id}",
            provider_payment_id=payment_id,
            expires_at=None,
        )

    async def verify_webhook(
        self, request_data: bytes, headers: dict
    ) -> bool:
        secret = settings.kingorder_secret_key
        if not secret:
            logger.warning("KingOrder secret key not configured, skipping verification")
            return True

        signature = headers.get("x-kingorder-signature", "")
        if not signature:
            logger.warning("Missing x-kingorder-signature header")
            return False

        expected = hmac.new(
            secret.encode(), request_data, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def parse_webhook(self, request_data: dict) -> PaymentResult:
        return PaymentResult(
            provider_payment_id=request_data.get("payment_id", ""),
            status=request_data.get("status", "completed"),
            amount=request_data.get("amount", 0),
            currency=request_data.get("currency", "KRW"),
            payment_method=request_data.get("payment_method"),
            paid_at=datetime.now(timezone.utc),
            raw_data=request_data,
        )

    async def get_payment_status(self, provider_payment_id: str) -> str:
        return "completed"

    async def refund(
        self, provider_payment_id: str, amount: float | None = None
    ) -> RefundResult:
        return RefundResult(
            provider_refund_id=f"ko_refund_{uuid.uuid4().hex[:8]}",
            status="completed",
            amount=amount or 0,
            raw_data={},
        )
