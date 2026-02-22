from datetime import datetime, timezone

from app.core.resilience import CircuitBreaker, get_http_client
from app.messenger.base import AbstractMessengerAdapter, StandardMessage
from app.messenger.factory import MessengerAdapterFactory
from app.models.messenger_account import MessengerAccount

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"

_circuit = CircuitBreaker("telegram")


class TelegramAdapter(AbstractMessengerAdapter):
    """Telegram Bot API adapter."""

    def _api_url(self, account: MessengerAccount, method: str) -> str:
        token = account.credentials["bot_token"]
        return f"{TELEGRAM_API_BASE.format(token=token)}/{method}"

    async def verify_webhook(
        self, request_data: bytes, headers: dict, *, secret: str | None = None
    ) -> bool:
        """Verify Telegram webhook using X-Telegram-Bot-Api-Secret-Token header."""
        if secret is None:
            return False
        token = headers.get("x-telegram-bot-api-secret-token")
        if token is None:
            return False
        return token == secret

    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        """Parse Telegram Update object into StandardMessage list."""
        message = request_data.get("message")
        if message is None:
            return []

        from_user = message.get("from", {})
        messenger_user_id = str(from_user.get("id", ""))
        messenger_message_id = str(message.get("message_id", ""))

        # Determine content type and content
        if "text" in message:
            content = message["text"]
            content_type = "text"
            attachments = []
        elif "photo" in message:
            content = message.get("caption", "")
            content_type = "image"
            # Use the largest photo (last in the array)
            largest_photo = message["photo"][-1]
            attachments = [{"file_id": largest_photo["file_id"], "type": "image"}]
        elif "document" in message:
            content = message.get("caption", "")
            content_type = "file"
            attachments = [
                {
                    "file_id": message["document"]["file_id"],
                    "type": "file",
                    "file_name": message["document"].get("file_name"),
                }
            ]
        elif "sticker" in message:
            content = message["sticker"].get("emoji", "")
            content_type = "sticker"
            attachments = [{"file_id": message["sticker"]["file_id"], "type": "sticker"}]
        else:
            return []

        timestamp = datetime.fromtimestamp(
            message.get("date", 0), tz=timezone.utc
        )

        return [
            StandardMessage(
                messenger_type="telegram",
                messenger_message_id=messenger_message_id,
                messenger_user_id=messenger_user_id,
                account_id=account.id,
                clinic_id=account.clinic_id,
                content=content,
                content_type=content_type,
                attachments=attachments,
                timestamp=timestamp,
                raw_data=request_data,
            )
        ]

    async def send_message(
        self,
        account: MessengerAccount,
        recipient_id: str,
        text: str,
        attachments: list[dict] | None = None,
    ) -> str:
        """Send a message via Telegram Bot API."""
        url = self._api_url(account, "sendMessage")
        payload = {
            "chat_id": recipient_id,
            "text": text,
            "parse_mode": "HTML",
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()

        data = await _circuit.call(_send)
        return str(data["result"]["message_id"])

    async def send_typing_indicator(
        self, account: MessengerAccount, recipient_id: str
    ) -> None:
        """Send typing action via Telegram Bot API."""
        url = self._api_url(account, "sendChatAction")
        payload = {
            "chat_id": recipient_id,
            "action": "typing",
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

        await _circuit.call(_send)

    async def get_user_profile(
        self, account: MessengerAccount, user_id: str
    ) -> dict:
        """Get user info via Telegram getChat API."""
        url = self._api_url(account, "getChat")

        async def _fetch():
            async with get_http_client() as client:
                response = await client.get(url, params={"chat_id": user_id})
                response.raise_for_status()
                return response.json()

        data = await _circuit.call(_fetch)
        return data["result"]


# Register adapter
MessengerAdapterFactory.register("telegram", TelegramAdapter)
