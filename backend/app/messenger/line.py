"""LINE Messaging API adapter.

- Webhook verification: X-Line-Signature (Base64 HMAC-SHA256)
- Send: Push API (proactive) / Reply API (within reply token window)
- API Base: https://api.line.me/v2/bot
"""

import base64
import hashlib
import hmac
import uuid
from datetime import datetime, timezone

from app.core.resilience import CircuitBreaker, get_http_client
from app.messenger.base import AbstractMessengerAdapter, StandardMessage
from app.messenger.factory import MessengerAdapterFactory
from app.models.messenger_account import MessengerAccount

LINE_API_BASE = "https://api.line.me/v2/bot"

_circuit = CircuitBreaker("line")


class LineAdapter(AbstractMessengerAdapter):
    """LINE Messaging API adapter."""

    async def verify_webhook(
        self, request_data: bytes, headers: dict, *, secret: str | None = None
    ) -> bool:
        """Verify X-Line-Signature (Base64 HMAC-SHA256)."""
        if secret is None:
            return False
        signature = headers.get("x-line-signature")
        if not signature:
            return False
        expected = base64.b64encode(
            hmac.new(secret.encode(), request_data, hashlib.sha256).digest()
        ).decode()
        return hmac.compare_digest(expected, signature)

    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        """Parse LINE webhook events into StandardMessage list."""
        messages: list[StandardMessage] = []
        for event in request_data.get("events", []):
            if event.get("type") != "message":
                continue

            source = event.get("source", {})
            user_id = source.get("userId", "")
            msg = event.get("message", {})
            msg_type = msg.get("type", "")
            msg_id = msg.get("id", "")
            timestamp_ms = event.get("timestamp", 0)
            ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

            if msg_type == "text":
                content = msg.get("text", "")
                content_type = "text"
                attachments = []
            elif msg_type == "image":
                content = ""
                content_type = "image"
                attachments = [{"type": "image", "message_id": msg_id}]
            elif msg_type == "video":
                content = ""
                content_type = "file"
                attachments = [{"type": "video", "message_id": msg_id}]
            elif msg_type == "sticker":
                content = ""
                content_type = "sticker"
                attachments = [
                    {
                        "type": "sticker",
                        "package_id": msg.get("packageId"),
                        "sticker_id": msg.get("stickerId"),
                    }
                ]
            else:
                continue

            messages.append(
                StandardMessage(
                    messenger_type="line",
                    messenger_message_id=msg_id,
                    messenger_user_id=user_id,
                    account_id=account.id,
                    clinic_id=account.clinic_id,
                    content=content,
                    content_type=content_type,
                    attachments=attachments,
                    timestamp=ts,
                    raw_data=request_data,
                )
            )
        return messages

    async def send_message(
        self,
        account: MessengerAccount,
        recipient_id: str,
        text: str,
        attachments: list[dict] | None = None,
    ) -> str:
        """Send message via LINE Push API."""
        token = account.credentials["channel_access_token"]
        url = f"{LINE_API_BASE}/message/push"
        payload = {
            "to": recipient_id,
            "messages": [{"type": "text", "text": text}],
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()

        await _circuit.call(_send)
        # LINE Push API doesn't return message_id; generate one for tracking
        return str(uuid.uuid4())

    async def send_typing_indicator(
        self, account: MessengerAccount, recipient_id: str
    ) -> None:
        """LINE does not have a typing indicator API; no-op."""
        pass

    async def get_user_profile(
        self, account: MessengerAccount, user_id: str
    ) -> dict:
        """Fetch user profile from LINE."""
        token = account.credentials["channel_access_token"]
        url = f"{LINE_API_BASE}/profile/{user_id}"

        async def _fetch():
            async with get_http_client() as client:
                response = await client.get(
                    url, headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                return response.json()

        return await _circuit.call(_fetch)


# Register adapter
MessengerAdapterFactory.register("line", LineAdapter)
