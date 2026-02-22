"""Stripe payment provider — real implementation using Stripe API."""

import logging
from datetime import datetime, timezone

import stripe

from app.config import settings
from app.core.resilience import retry_async
from app.payment.base import (
    AbstractPaymentProvider,
    PaymentLinkResult,
    PaymentResult,
    RefundResult,
)

logger = logging.getLogger(__name__)


class StripeProvider(AbstractPaymentProvider):
    """Stripe payment provider with Checkout Sessions."""

    def __init__(self):
        stripe.api_key = settings.stripe_secret_key

    @retry_async(retry_on=(stripe.error.APIConnectionError, stripe.error.RateLimitError))
    async def create_payment_link(
        self, amount: float, currency: str, metadata: dict | None = None
    ) -> PaymentLinkResult:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": int(amount * 100),
                    "product_data": {"name": "Medical procedure payment"},
                },
                "quantity": 1,
            }],
            mode="payment",
            metadata=metadata or {},
            success_url=f"{settings.cors_origins.split(',')[0]}/payments/success"
                        "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=f"{settings.cors_origins.split(',')[0]}/payments/cancel",
        )
        return PaymentLinkResult(
            link=session.url,
            qr_url=None,
            provider_payment_id=session.payment_intent or session.id,
            expires_at=None,
        )

    async def verify_webhook(
        self, request_data: bytes, headers: dict
    ) -> bool:
        sig = headers.get("stripe-signature", "")
        try:
            stripe.Webhook.construct_event(
                request_data, sig, settings.stripe_webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            logger.warning("Stripe webhook signature verification failed")
            return False

    async def parse_webhook(self, request_data: dict) -> PaymentResult:
        event = stripe.Event.construct_from(request_data, stripe.api_key)
        data = event.data.object

        status_map = {
            "payment_intent.succeeded": "completed",
            "payment_intent.payment_failed": "failed",
            "checkout.session.completed": "completed",
        }
        status = status_map.get(event.type, "pending")

        return PaymentResult(
            provider_payment_id=data.get("payment_intent", data.get("id", "")),
            status=status,
            amount=data.get("amount_total", data.get("amount", 0)) / 100,
            currency=data.get("currency", "usd").upper(),
            payment_method=data.get("payment_method_types", ["card"])[0]
            if isinstance(data.get("payment_method_types"), list)
            else "card",
            paid_at=datetime.now(timezone.utc) if status == "completed" else None,
            raw_data=request_data,
        )

    @retry_async(retry_on=(stripe.error.APIConnectionError, stripe.error.RateLimitError))
    async def get_payment_status(self, provider_payment_id: str) -> str:
        pi = stripe.PaymentIntent.retrieve(provider_payment_id)
        return {
            "succeeded": "completed",
            "requires_payment_method": "pending",
            "requires_confirmation": "pending",
            "processing": "pending",
            "canceled": "failed",
        }.get(pi.status, pi.status)

    @retry_async(retry_on=(stripe.error.APIConnectionError, stripe.error.RateLimitError))
    async def refund(
        self, provider_payment_id: str, amount: float | None = None
    ) -> RefundResult:
        params = {"payment_intent": provider_payment_id}
        if amount is not None:
            params["amount"] = int(amount * 100)
        refund = stripe.Refund.create(**params)
        return RefundResult(
            provider_refund_id=refund.id,
            status="completed" if refund.status == "succeeded" else refund.status,
            amount=refund.amount / 100,
            raw_data={"refund_id": refund.id, "status": refund.status},
        )
