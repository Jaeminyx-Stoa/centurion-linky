from app.messenger.base import AbstractMessengerAdapter


class MessengerAdapterFactory:
    """Factory to get the correct messenger adapter by type."""

    _adapters: dict[str, type[AbstractMessengerAdapter]] = {}

    @classmethod
    def register(cls, messenger_type: str, adapter_class: type[AbstractMessengerAdapter]):
        cls._adapters[messenger_type] = adapter_class

    @classmethod
    def get_adapter(cls, messenger_type: str) -> AbstractMessengerAdapter:
        adapter_class = cls._adapters.get(messenger_type)
        if adapter_class is None:
            raise ValueError(f"Unsupported messenger type: {messenger_type}")
        return adapter_class()

    @classmethod
    def supported_types(cls) -> list[str]:
        return list(cls._adapters.keys())
