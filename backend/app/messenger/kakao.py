"""KakaoTalk Channel API adapter.

- Webhook: Skill-based chatbot payload (userRequest format)
- Send: REST API for friendtalk messages
- API Base: https://kapi.kakao.com
"""

import uuid
from datetime import datetime, timezone

import httpx

from app.messenger.base import AbstractMessengerAdapter, StandardMessage
from app.messenger.factory import MessengerAdapterFactory
from app.models.messenger_account import MessengerAccount

KAKAO_API_BASE = "https://kapi.kakao.com"


class KakaoAdapter(AbstractMessengerAdapter):
    """KakaoTalk Channel chatbot adapter."""

    async def verify_webhook(
        self, request_data: bytes, headers: dict, *, secret: str | None = None
    ) -> bool:
        """Verify KakaoTalk webhook via X-Kakao-Bot-Verification header."""
        if secret is None:
            return False
        token = headers.get("x-kakao-bot-verification")
        if not token:
            return False
        return token == secret

    async def parse_webhook(
        self, account: MessengerAccount, request_data: dict
    ) -> list[StandardMessage]:
        """Parse KakaoTalk skill chatbot webhook payload."""
        user_request = request_data.get("userRequest")
        if not user_request:
            return []

        user = user_request.get("user", {})
        user_id = user.get("id", "")
        utterance = user_request.get("utterance", "")

        # Check for media attachments
        params = user_request.get("params", {})
        media = params.get("media") if isinstance(params, dict) else None

        if media and isinstance(media, dict):
            content_type = media.get("type", "file")
            attachments = [{"type": media["type"], "url": media.get("url")}]
        else:
            content_type = "text"
            attachments = []

        # Generate message ID from block + timestamp
        block = user_request.get("block", {})
        msg_id = f"kakao_{block.get('id', '')}_{int(datetime.now(tz=timezone.utc).timestamp())}"

        return [
            StandardMessage(
                messenger_type="kakao",
                messenger_message_id=msg_id,
                messenger_user_id=user_id,
                account_id=account.id,
                clinic_id=account.clinic_id,
                content=utterance,
                content_type=content_type,
                attachments=attachments,
                timestamp=datetime.now(tz=timezone.utc),
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
        """Send message via KakaoTalk Channel API (friendtalk)."""
        api_key = account.credentials.get("api_key", "")
        url = f"{KAKAO_API_BASE}/v1/api/talk/friends/message/default/send"
        payload = {
            "receiver_uuids": [recipient_id],
            "template_object": {
                "object_type": "text",
                "text": text,
                "link": {},
            },
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        return str(uuid.uuid4())

    async def send_typing_indicator(
        self, account: MessengerAccount, recipient_id: str
    ) -> None:
        """KakaoTalk does not support typing indicators; no-op."""
        pass

    async def get_user_profile(
        self, account: MessengerAccount, user_id: str
    ) -> dict:
        """KakaoTalk user profile is limited in channel API."""
        return {"user_id": user_id}


# Register adapter
MessengerAdapterFactory.register("kakao", KakaoAdapter)
