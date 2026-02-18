import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.messenger_account import MessengerAccount


@dataclass
class StandardMessage:
    """Unified message format across all messenger platforms."""

    messenger_type: str
    messenger_message_id: str
    messenger_user_id: str
    account_id: uuid.UUID
    clinic_id: uuid.UUID
    content: str
    content_type: str = "text"  # 'text','image','file','sticker'
    attachments: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_data: dict = field(default_factory=dict)


class AbstractMessengerAdapter(ABC):
    """Base interface for all messenger adapters."""

    @abstractmethod
    async def verify_webhook(self, request_data: bytes, headers: dict) -> bool:
        """Verify webhook request signature."""

    @abstractmethod
    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        """Parse webhook payload into StandardMessage list."""

    @abstractmethod
    async def send_message(
        self,
        account: MessengerAccount,
        recipient_id: str,
        text: str,
        attachments: list[dict] | None = None,
    ) -> str:
        """Send a message. Returns messenger_message_id."""

    @abstractmethod
    async def send_typing_indicator(
        self, account: MessengerAccount, recipient_id: str
    ) -> None:
        """Show typing indicator to recipient."""

    @abstractmethod
    async def get_user_profile(
        self, account: MessengerAccount, user_id: str
    ) -> dict:
        """Fetch user profile information."""
