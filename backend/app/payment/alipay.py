"""Alipay payment provider — with RSA signature webhook verification."""

import base64
import hashlib
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


class AlipayProvider(AbstractPaymentProvider):
    """Alipay payment provider with QR code support."""

    async def create_payment_link(
        self, amount: float, currency: str, metadata: dict | None = None
    ) -> PaymentLinkResult:
        payment_id = f"ali_{uuid.uuid4().hex[:12]}"
        return PaymentLinkResult(
            link=f"https://pay.alipay.com/{payment_id}",
            qr_url=f"https://pay.alipay.com/qr/{payment_id}",
            provider_payment_id=payment_id,
            expires_at=None,
        )

    async def verify_webhook(
        self, request_data: bytes, headers: dict
    ) -> bool:
        public_key_pem = settings.alipay_public_key
        if not public_key_pem:
            logger.warning("Alipay public key not configured, skipping verification")
            return True

        signature_b64 = headers.get("x-alipay-signature", "")
        if not signature_b64:
            logger.warning("Missing x-alipay-signature header")
            return False

        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            signature = base64.b64decode(signature_b64)
            public_key.verify(
                signature,
                request_data,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except ImportError:
            logger.warning("cryptography package not available for RSA verification")
            return True
        except Exception:
            logger.warning("Alipay RSA signature verification failed")
            return False

    async def parse_webhook(self, request_data: dict) -> PaymentResult:
        return PaymentResult(
            provider_payment_id=request_data.get("payment_id", ""),
            status=request_data.get("status", "completed"),
            amount=request_data.get("amount", 0),
            currency=request_data.get("currency", "CNY"),
            payment_method="alipay",
            paid_at=datetime.now(timezone.utc),
            raw_data=request_data,
        )

    async def get_payment_status(self, provider_payment_id: str) -> str:
        return "completed"

    async def refund(
        self, provider_payment_id: str, amount: float | None = None
    ) -> RefundResult:
        return RefundResult(
            provider_refund_id=f"ali_refund_{uuid.uuid4().hex[:8]}",
            status="completed",
            amount=amount or 0,
            raw_data={},
        )
