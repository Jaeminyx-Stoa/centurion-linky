from app.payment.alipay import AlipayProvider
from app.payment.base import AbstractPaymentProvider
from app.payment.kingorder import KingOrderProvider
from app.payment.stripe_provider import StripeProvider
from app.payment.stub import StubProvider

_PROVIDERS: dict[str, type[AbstractPaymentProvider]] = {
    "stub": StubProvider,
    "kingorder": KingOrderProvider,
    "alipay": AlipayProvider,
    "stripe": StripeProvider,
}

# country + payment_method → provider routing
_ROUTING: dict[tuple[str, str], str] = {
    ("JP", "line_pay"): "kingorder",
    ("JP", "card"): "kingorder",
    ("KR", "kakao_pay"): "kingorder",
    ("KR", "card"): "kingorder",
    ("TW", "line_pay"): "kingorder",
    ("TW", "card"): "kingorder",
    ("CN", "alipay"): "alipay",
}


class PaymentProviderFactory:
    """Factory to get the correct payment provider."""

    @staticmethod
    def get_provider(provider_type: str) -> AbstractPaymentProvider:
        provider_class = _PROVIDERS.get(provider_type)
        if provider_class is None:
            raise ValueError(f"Unsupported payment provider: {provider_type}")
        return provider_class()

    @staticmethod
    def get_provider_for(
        country_code: str | None = None,
        payment_method: str | None = None,
    ) -> tuple[str, AbstractPaymentProvider]:
        """Route to a provider based on country + payment method.

        Returns (provider_type, provider_instance).
        """
        if country_code and payment_method:
            key = (country_code.upper(), payment_method)
            provider_type = _ROUTING.get(key)
            if provider_type:
                return provider_type, _PROVIDERS[provider_type]()

        # Fallback to stripe
        return "stripe", StripeProvider()

    @staticmethod
    def supported_providers() -> list[str]:
        return list(_PROVIDERS.keys())
