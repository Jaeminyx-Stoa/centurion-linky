"""Tests for Stripe webhook signature verification and parsing."""

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from app.payment.stripe_provider import StripeProvider


class TestStripeWebhookVerification:
    @pytest.mark.asyncio
    @patch("app.payment.stripe_provider.stripe")
    async def test_verify_webhook_valid_signature(self, mock_stripe):
        """Valid signature should return True."""
        mock_stripe.Webhook.construct_event.return_value = {"type": "payment_intent.succeeded"}
        provider = StripeProvider.__new__(StripeProvider)

        result = await provider.verify_webhook(
            b'{"type": "payment_intent.succeeded"}',
            {"stripe-signature": "t=123,v1=abc"},
        )
        assert result is True

    @pytest.mark.asyncio
    @patch("app.payment.stripe_provider.stripe")
    async def test_verify_webhook_invalid_signature(self, mock_stripe):
        """Invalid signature should return False."""
        import stripe as stripe_pkg
        mock_stripe.error = stripe_pkg.error
        mock_stripe.Webhook.construct_event.side_effect = (
            stripe_pkg.error.SignatureVerificationError("bad sig", "sig_header")
        )
        provider = StripeProvider.__new__(StripeProvider)

        result = await provider.verify_webhook(
            b'{"type": "payment_intent.succeeded"}',
            {"stripe-signature": "t=123,v1=bad"},
        )
        assert result is False


class TestStripeWebhookParsing:
    @pytest.mark.asyncio
    @patch("app.payment.stripe_provider.stripe")
    async def test_parse_webhook_payment_succeeded(self, mock_stripe):
        """payment_intent.succeeded event should parse to 'completed'."""
        mock_event = MagicMock()
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object = {
            "payment_intent": "pi_test123",
            "amount_total": 50000,
            "currency": "usd",
            "payment_method_types": ["card"],
        }
        mock_stripe.Event.construct_from.return_value = mock_event

        provider = StripeProvider.__new__(StripeProvider)
        result = await provider.parse_webhook({"type": "payment_intent.succeeded"})

        assert result.status == "completed"
        assert result.provider_payment_id == "pi_test123"
        assert result.amount == 500.0  # 50000 cents / 100

    @pytest.mark.asyncio
    @patch("app.payment.stripe_provider.stripe")
    async def test_parse_webhook_payment_failed(self, mock_stripe):
        """payment_intent.payment_failed event should parse to 'failed'."""
        mock_event = MagicMock()
        mock_event.type = "payment_intent.payment_failed"
        mock_event.data.object = {
            "payment_intent": "pi_fail123",
            "amount_total": 10000,
            "currency": "krw",
            "payment_method_types": ["card"],
        }
        mock_stripe.Event.construct_from.return_value = mock_event

        provider = StripeProvider.__new__(StripeProvider)
        result = await provider.parse_webhook({"type": "payment_intent.payment_failed"})

        assert result.status == "failed"
        assert result.paid_at is None


class TestKingOrderWebhookVerification:
    @pytest.mark.asyncio
    async def test_verify_webhook_valid_hmac(self):
        """Valid HMAC-SHA256 signature should return True."""
        from app.payment.kingorder import KingOrderProvider

        provider = KingOrderProvider()
        secret = "test_secret_key"
        body = b'{"payment_id": "ko_123", "status": "completed"}'
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        with patch("app.payment.kingorder.settings") as mock_settings:
            mock_settings.kingorder_secret_key = secret
            result = await provider.verify_webhook(
                body, {"x-kingorder-signature": signature}
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_webhook_invalid_hmac(self):
        """Invalid HMAC signature should return False."""
        from app.payment.kingorder import KingOrderProvider

        provider = KingOrderProvider()

        with patch("app.payment.kingorder.settings") as mock_settings:
            mock_settings.kingorder_secret_key = "test_secret"
            result = await provider.verify_webhook(
                b'{"data": "test"}', {"x-kingorder-signature": "bad_signature"}
            )
        assert result is False
