import pytest

from app.payment.alipay import AlipayProvider
from app.payment.factory import PaymentProviderFactory
from app.payment.kingorder import KingOrderProvider
from app.payment.stripe_provider import StripeProvider
from app.payment.stub import StubProvider


class TestGetProvider:
    def test_get_stub(self):
        provider = PaymentProviderFactory.get_provider("stub")
        assert isinstance(provider, StubProvider)

    def test_get_unsupported_raises(self):
        with pytest.raises(ValueError, match="Unsupported payment provider"):
            PaymentProviderFactory.get_provider("nonexistent")


class TestGetProviderFor:
    def test_kr_kakao_routes_to_kingorder(self):
        ptype, provider = PaymentProviderFactory.get_provider_for("KR", "kakao_pay")
        assert ptype == "kingorder"
        assert isinstance(provider, KingOrderProvider)

    def test_jp_line_routes_to_kingorder(self):
        ptype, provider = PaymentProviderFactory.get_provider_for("JP", "line_pay")
        assert ptype == "kingorder"
        assert isinstance(provider, KingOrderProvider)

    def test_cn_alipay_routes_to_alipay(self):
        ptype, provider = PaymentProviderFactory.get_provider_for("CN", "alipay")
        assert ptype == "alipay"
        assert isinstance(provider, AlipayProvider)

    def test_fallback_to_stripe(self):
        ptype, provider = PaymentProviderFactory.get_provider_for("US", "card")
        assert ptype == "stripe"
        assert isinstance(provider, StripeProvider)

    def test_none_country_fallback(self):
        ptype, provider = PaymentProviderFactory.get_provider_for(None, None)
        assert ptype == "stripe"


class TestSupportedProviders:
    def test_lists_all(self):
        providers = PaymentProviderFactory.supported_providers()
        assert "stub" in providers
        assert "kingorder" in providers
        assert "alipay" in providers
        assert "stripe" in providers
