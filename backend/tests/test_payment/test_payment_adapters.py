import pytest

from app.payment.alipay import AlipayProvider
from app.payment.base import (
    AbstractPaymentProvider,
    PaymentLinkResult,
    PaymentResult,
    RefundResult,
)
from app.payment.kingorder import KingOrderProvider
from app.payment.stripe_provider import StripeProvider
from app.payment.stub import StubProvider


class TestDataclasses:
    def test_payment_link_result(self):
        result = PaymentLinkResult(
            link="https://pay.example.com/123",
            qr_url="https://pay.example.com/qr/123",
            provider_payment_id="pay_123",
        )
        assert result.link == "https://pay.example.com/123"
        assert result.qr_url == "https://pay.example.com/qr/123"
        assert result.provider_payment_id == "pay_123"
        assert result.expires_at is None

    def test_payment_result_defaults(self):
        result = PaymentResult(
            provider_payment_id="pay_456",
            status="completed",
            amount=50000,
            currency="KRW",
        )
        assert result.payment_method is None
        assert result.paid_at is None
        assert result.raw_data == {}


class TestAbstractInterface:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            AbstractPaymentProvider()


class TestStubProvider:
    @pytest.mark.asyncio
    async def test_create_payment_link(self):
        provider = StubProvider()
        result = await provider.create_payment_link(50000, "KRW")
        assert result.link.startswith("https://pay.stub.dev/")
        assert result.qr_url is not None
        assert result.provider_payment_id.startswith("stub_")

    @pytest.mark.asyncio
    async def test_verify_webhook_always_true(self):
        provider = StubProvider()
        assert await provider.verify_webhook(b"{}", {}) is True

    @pytest.mark.asyncio
    async def test_parse_webhook(self):
        provider = StubProvider()
        result = await provider.parse_webhook({
            "payment_id": "stub_abc",
            "status": "completed",
            "amount": 100000,
            "currency": "KRW",
        })
        assert isinstance(result, PaymentResult)
        assert result.provider_payment_id == "stub_abc"
        assert result.status == "completed"
        assert result.amount == 100000

    @pytest.mark.asyncio
    async def test_get_payment_status(self):
        provider = StubProvider()
        status = await provider.get_payment_status("stub_abc")
        assert status == "completed"

    @pytest.mark.asyncio
    async def test_refund(self):
        provider = StubProvider()
        result = await provider.refund("stub_abc", 50000)
        assert isinstance(result, RefundResult)
        assert result.status == "completed"
        assert result.amount == 50000


class TestKingOrderProvider:
    @pytest.mark.asyncio
    async def test_create_payment_link(self):
        provider = KingOrderProvider()
        result = await provider.create_payment_link(100000, "KRW")
        assert result.link.startswith("https://pay.kingorder.kr/")
        assert result.provider_payment_id.startswith("ko_")


class TestAlipayProvider:
    @pytest.mark.asyncio
    async def test_create_payment_link(self):
        provider = AlipayProvider()
        result = await provider.create_payment_link(500, "CNY")
        assert result.link.startswith("https://pay.alipay.com/")
        assert result.provider_payment_id.startswith("ali_")


class TestStripeProvider:
    @pytest.mark.asyncio
    async def test_create_payment_link(self):
        provider = StripeProvider()
        result = await provider.create_payment_link(50, "USD")
        assert result.link.startswith("https://checkout.stripe.com/")
        assert result.provider_payment_id.startswith("pi_")
        assert result.qr_url is None
