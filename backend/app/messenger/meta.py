"""Meta Platform adapters: Instagram DM, Facebook Messenger, WhatsApp Cloud API.

All three share HMAC-SHA256 webhook verification via X-Hub-Signature-256.
Instagram/Facebook use the Messenger Send API; WhatsApp uses the Cloud API.
"""

import hashlib
import hmac
from datetime import datetime, timezone

from app.core.resilience import CircuitBreaker, get_http_client
from app.messenger.base import AbstractMessengerAdapter, StandardMessage
from app.messenger.factory import MessengerAdapterFactory
from app.models.messenger_account import MessengerAccount

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

_circuit = CircuitBreaker("meta_graph_api")


class MetaBaseAdapter(AbstractMessengerAdapter):
    """Shared logic for all Meta Platform messengers."""

    messenger_type: str = ""  # Override in subclasses

    async def verify_webhook(
        self, request_data: bytes, headers: dict, *, secret: str | None = None
    ) -> bool:
        """Verify X-Hub-Signature-256 HMAC-SHA256 signature."""
        if secret is None:
            return False
        signature_header = headers.get("x-hub-signature-256")
        if not signature_header:
            return False
        expected = "sha256=" + hmac.new(
            secret.encode(), request_data, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    async def send_typing_indicator(
        self, account: MessengerAccount, recipient_id: str
    ) -> None:
        """Send typing indicator via Messenger Send API."""
        token = account.credentials.get("page_access_token") or account.credentials.get("access_token")
        url = f"{GRAPH_API_BASE}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "sender_action": "typing_on",
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(
                    url, json=payload, params={"access_token": token}
                )
                response.raise_for_status()

        await _circuit.call(_send)

    async def get_user_profile(
        self, account: MessengerAccount, user_id: str
    ) -> dict:
        """Fetch user profile from Graph API."""
        token = account.credentials.get("page_access_token") or account.credentials.get("access_token")
        url = f"{GRAPH_API_BASE}/{user_id}"

        async def _fetch():
            async with get_http_client() as client:
                response = await client.get(
                    url,
                    params={
                        "fields": "name,profile_pic",
                        "access_token": token,
                    },
                )
                response.raise_for_status()
                return response.json()

        return await _circuit.call(_fetch)


# ============================================================
# Instagram DM Adapter
# ============================================================
class InstagramAdapter(MetaBaseAdapter):
    """Instagram DM adapter via Messenger Platform."""

    messenger_type = "instagram"

    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        messages: list[StandardMessage] = []
        for entry in request_data.get("entry", []):
            for event in entry.get("messaging", []):
                msg_data = event.get("message")
                if not msg_data:
                    continue

                sender_id = event["sender"]["id"]
                mid = msg_data.get("mid", "")
                timestamp_ms = event.get("timestamp", 0)
                ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

                # Determine content type
                attachments_data = msg_data.get("attachments", [])
                if attachments_data:
                    att = attachments_data[0]
                    content_type = att.get("type", "file")
                    content = msg_data.get("text", "")
                    attachments = [
                        {"type": att["type"], "url": att.get("payload", {}).get("url")}
                    ]
                else:
                    content = msg_data.get("text", "")
                    content_type = "text"
                    attachments = []

                messages.append(
                    StandardMessage(
                        messenger_type=self.messenger_type,
                        messenger_message_id=mid,
                        messenger_user_id=sender_id,
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
        """Send message via Messenger Send API (Instagram)."""
        token = account.credentials["page_access_token"]
        url = f"{GRAPH_API_BASE}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(
                    url, json=payload, params={"access_token": token}
                )
                response.raise_for_status()
                return response.json()

        data = await _circuit.call(_send)
        return data.get("message_id", "")


# ============================================================
# Facebook Messenger Adapter
# ============================================================
class FacebookAdapter(MetaBaseAdapter):
    """Facebook Messenger adapter."""

    messenger_type = "facebook"

    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        messages: list[StandardMessage] = []
        for entry in request_data.get("entry", []):
            for event in entry.get("messaging", []):
                msg_data = event.get("message")
                if not msg_data:
                    continue

                sender_id = event["sender"]["id"]
                mid = msg_data.get("mid", "")
                timestamp_ms = event.get("timestamp", 0)
                ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

                attachments_data = msg_data.get("attachments", [])
                if attachments_data:
                    att = attachments_data[0]
                    content_type = att.get("type", "file")
                    content = msg_data.get("text", "")
                    attachments = [
                        {"type": att["type"], "url": att.get("payload", {}).get("url")}
                    ]
                else:
                    content = msg_data.get("text", "")
                    content_type = "text"
                    attachments = []

                messages.append(
                    StandardMessage(
                        messenger_type=self.messenger_type,
                        messenger_message_id=mid,
                        messenger_user_id=sender_id,
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
        """Send message via Messenger Send API (Facebook)."""
        token = account.credentials["page_access_token"]
        url = f"{GRAPH_API_BASE}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(
                    url, json=payload, params={"access_token": token}
                )
                response.raise_for_status()
                return response.json()

        data = await _circuit.call(_send)
        return data.get("message_id", "")


# ============================================================
# WhatsApp Cloud API Adapter
# ============================================================
class WhatsAppAdapter(MetaBaseAdapter):
    """WhatsApp Business Cloud API adapter."""

    messenger_type = "whatsapp"

    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        messages: list[StandardMessage] = []
        for entry in request_data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg_data in value.get("messages", []):
                    sender = msg_data.get("from", "")
                    wamid = msg_data.get("id", "")
                    timestamp_str = msg_data.get("timestamp", "0")
                    ts = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)

                    msg_type = msg_data.get("type", "")
                    if msg_type == "text":
                        content = msg_data.get("text", {}).get("body", "")
                        content_type = "text"
                        attachments = []
                    elif msg_type == "image":
                        img = msg_data.get("image", {})
                        content = img.get("caption", "")
                        content_type = "image"
                        attachments = [
                            {"type": "image", "media_id": img.get("id"), "mime_type": img.get("mime_type")}
                        ]
                    elif msg_type == "document":
                        doc = msg_data.get("document", {})
                        content = doc.get("caption", "")
                        content_type = "file"
                        attachments = [
                            {"type": "file", "media_id": doc.get("id"), "filename": doc.get("filename")}
                        ]
                    elif msg_type == "sticker":
                        sticker = msg_data.get("sticker", {})
                        content = ""
                        content_type = "sticker"
                        attachments = [{"type": "sticker", "media_id": sticker.get("id")}]
                    else:
                        continue

                    messages.append(
                        StandardMessage(
                            messenger_type=self.messenger_type,
                            messenger_message_id=wamid,
                            messenger_user_id=sender,
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
        """Send message via WhatsApp Cloud API."""
        token = account.credentials["access_token"]
        phone_number_id = account.credentials["phone_number_id"]
        url = f"{GRAPH_API_BASE}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text},
        }

        async def _send():
            async with get_http_client() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                return response.json()

        data = await _circuit.call(_send)
        return data.get("messages", [{}])[0].get("id", "")

    async def send_typing_indicator(
        self, account: MessengerAccount, recipient_id: str
    ) -> None:
        """WhatsApp does not support typing indicators directly; no-op."""
        pass

    async def get_user_profile(
        self, account: MessengerAccount, user_id: str
    ) -> dict:
        """WhatsApp Cloud API doesn't expose user profiles directly."""
        return {"phone": user_id}


# Register all Meta adapters
MessengerAdapterFactory.register("instagram", InstagramAdapter)
MessengerAdapterFactory.register("facebook", FacebookAdapter)
MessengerAdapterFactory.register("whatsapp", WhatsAppAdapter)
