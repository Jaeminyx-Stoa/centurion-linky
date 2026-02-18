"""Tests for Meta Platform adapters (Instagram, Facebook, WhatsApp)."""

import hashlib
import hmac
import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messenger.base import StandardMessage
from app.messenger.meta import (
    FacebookAdapter,
    InstagramAdapter,
    MetaBaseAdapter,
    WhatsAppAdapter,
)
from app.models.messenger_account import MessengerAccount


APP_SECRET = "test_app_secret_12345"


@pytest.fixture
def instagram_adapter():
    return InstagramAdapter()


@pytest.fixture
def facebook_adapter():
    return FacebookAdapter()


@pytest.fixture
def whatsapp_adapter():
    return WhatsAppAdapter()


@pytest.fixture
def ig_account():
    return MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        messenger_type="instagram",
        account_name="clinic_ig",
        credentials={
            "page_access_token": "EAAxxxxxxxx",
            "app_secret": APP_SECRET,
            "page_id": "111222333",
        },
        webhook_secret="ig_verify_token",
    )


@pytest.fixture
def fb_account():
    return MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        messenger_type="facebook",
        account_name="clinic_fb",
        credentials={
            "page_access_token": "EAAxxxxxxxx",
            "app_secret": APP_SECRET,
            "page_id": "444555666",
        },
        webhook_secret="fb_verify_token",
    )


@pytest.fixture
def wa_account():
    return MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        messenger_type="whatsapp",
        account_name="clinic_wa",
        credentials={
            "access_token": "EAAxxxxxxxx",
            "app_secret": APP_SECRET,
            "phone_number_id": "109876543210",
        },
        webhook_secret="wa_verify_token",
    )


def _make_signature(body: bytes, secret: str) -> str:
    """Generate X-Hub-Signature-256 header value."""
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


# ============================================================
# Instagram Adapter Tests
# ============================================================
class TestInstagramVerifyWebhook:
    async def test_verify_valid_signature(self, instagram_adapter, ig_account):
        body = b'{"entry": []}'
        headers = {
            "x-hub-signature-256": _make_signature(body, APP_SECRET),
        }
        result = await instagram_adapter.verify_webhook(
            body, headers, secret=APP_SECRET
        )
        assert result is True

    async def test_verify_invalid_signature(self, instagram_adapter, ig_account):
        body = b'{"entry": []}'
        headers = {"x-hub-signature-256": "sha256=invalid"}
        result = await instagram_adapter.verify_webhook(
            body, headers, secret=APP_SECRET
        )
        assert result is False

    async def test_verify_missing_signature(self, instagram_adapter, ig_account):
        result = await instagram_adapter.verify_webhook(b"", {}, secret=APP_SECRET)
        assert result is False


class TestInstagramParseWebhook:
    async def test_parse_text_message(self, instagram_adapter, ig_account):
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": "111222333",
                    "time": 1700000000,
                    "messaging": [
                        {
                            "sender": {"id": "9876543210"},
                            "recipient": {"id": "111222333"},
                            "timestamp": 1700000000000,
                            "message": {
                                "mid": "m_abc123",
                                "text": "ボトックスの料金は？",
                            },
                        }
                    ],
                }
            ],
        }

        messages = await instagram_adapter.parse_webhook(ig_account, payload)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.messenger_type == "instagram"
        assert msg.messenger_user_id == "9876543210"
        assert msg.messenger_message_id == "m_abc123"
        assert msg.content == "ボトックスの料金は？"
        assert msg.content_type == "text"

    async def test_parse_image_message(self, instagram_adapter, ig_account):
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": "111222333",
                    "time": 1700000000,
                    "messaging": [
                        {
                            "sender": {"id": "9876543210"},
                            "recipient": {"id": "111222333"},
                            "timestamp": 1700000000000,
                            "message": {
                                "mid": "m_img456",
                                "attachments": [
                                    {
                                        "type": "image",
                                        "payload": {
                                            "url": "https://cdn.example.com/photo.jpg"
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        messages = await instagram_adapter.parse_webhook(ig_account, payload)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.content_type == "image"
        assert msg.attachments[0]["url"] == "https://cdn.example.com/photo.jpg"

    async def test_parse_empty_entry(self, instagram_adapter, ig_account):
        payload = {"object": "instagram", "entry": []}
        messages = await instagram_adapter.parse_webhook(ig_account, payload)
        assert messages == []


class TestInstagramSendMessage:
    async def test_send_text(self, instagram_adapter, ig_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"recipient_id": "9876543210", "message_id": "m_sent1"}

        with patch("app.messenger.meta.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            msg_id = await instagram_adapter.send_message(
                ig_account, "9876543210", "안녕하세요!"
            )

        assert msg_id == "m_sent1"
        call_args = mock_client.post.call_args
        assert "me/messages" in call_args[0][0]


# ============================================================
# Facebook Adapter Tests
# ============================================================
class TestFacebookParseWebhook:
    async def test_parse_text_message(self, facebook_adapter, fb_account):
        payload = {
            "object": "page",
            "entry": [
                {
                    "id": "444555666",
                    "time": 1700000000,
                    "messaging": [
                        {
                            "sender": {"id": "1234567890"},
                            "recipient": {"id": "444555666"},
                            "timestamp": 1700000000000,
                            "message": {
                                "mid": "m_fb_abc",
                                "text": "Hello, I want to book",
                            },
                        }
                    ],
                }
            ],
        }

        messages = await facebook_adapter.parse_webhook(fb_account, payload)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.messenger_type == "facebook"
        assert msg.content == "Hello, I want to book"


# ============================================================
# WhatsApp Adapter Tests
# ============================================================
class TestWhatsAppParseWebhook:
    async def test_parse_text_message(self, whatsapp_adapter, wa_account):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "BIZ_ACCT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "821012345678",
                                    "phone_number_id": "109876543210",
                                },
                                "messages": [
                                    {
                                        "from": "819012345678",
                                        "id": "wamid.abc123",
                                        "timestamp": "1700000000",
                                        "type": "text",
                                        "text": {"body": "I'd like to inquire about Botox"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        messages = await whatsapp_adapter.parse_webhook(wa_account, payload)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.messenger_type == "whatsapp"
        assert msg.messenger_user_id == "819012345678"
        assert msg.messenger_message_id == "wamid.abc123"
        assert msg.content == "I'd like to inquire about Botox"
        assert msg.content_type == "text"

    async def test_parse_image_message(self, whatsapp_adapter, wa_account):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "BIZ_ACCT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "821012345678",
                                    "phone_number_id": "109876543210",
                                },
                                "messages": [
                                    {
                                        "from": "819012345678",
                                        "id": "wamid.img456",
                                        "timestamp": "1700000000",
                                        "type": "image",
                                        "image": {
                                            "id": "img_media_id",
                                            "mime_type": "image/jpeg",
                                            "caption": "참고 사진",
                                        },
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        messages = await whatsapp_adapter.parse_webhook(wa_account, payload)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.content_type == "image"
        assert msg.content == "참고 사진"

    async def test_parse_status_update_ignored(self, whatsapp_adapter, wa_account):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "BIZ_ACCT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "109876543210"},
                                "statuses": [
                                    {"id": "wamid.xxx", "status": "delivered"}
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        messages = await whatsapp_adapter.parse_webhook(wa_account, payload)
        assert messages == []


class TestWhatsAppSendMessage:
    async def test_send_text(self, whatsapp_adapter, wa_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "messages": [{"id": "wamid.sent1"}],
        }

        with patch("app.messenger.meta.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            msg_id = await whatsapp_adapter.send_message(
                wa_account, "819012345678", "안녕하세요!"
            )

        assert msg_id == "wamid.sent1"
        call_args = mock_client.post.call_args
        assert "109876543210" in call_args[0][0]


# ============================================================
# Factory Registration Tests
# ============================================================
class TestMetaFactoryRegistration:
    def test_all_meta_adapters_registered(self):
        from app.messenger.factory import MessengerAdapterFactory

        supported = MessengerAdapterFactory.supported_types()
        assert "instagram" in supported
        assert "facebook" in supported
        assert "whatsapp" in supported
