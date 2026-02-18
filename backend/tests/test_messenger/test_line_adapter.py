"""Tests for LINE Messaging API adapter."""

import base64
import hashlib
import hmac
import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messenger.base import StandardMessage
from app.messenger.line import LineAdapter
from app.models.messenger_account import MessengerAccount


CHANNEL_SECRET = "test_channel_secret"


@pytest.fixture
def line_adapter():
    return LineAdapter()


@pytest.fixture
def line_account():
    return MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        messenger_type="line",
        account_name="clinic_line",
        credentials={
            "channel_access_token": "line_token_xxxxx",
            "channel_secret": CHANNEL_SECRET,
        },
        webhook_secret=CHANNEL_SECRET,
    )


def _make_line_signature(body: bytes, secret: str) -> str:
    """Generate X-Line-Signature header value (Base64 HMAC-SHA256)."""
    return base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()


@pytest.fixture
def line_text_event():
    return {
        "destination": "Uxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "12345678901234",
                    "text": "ボトックスの料金を教えてください",
                },
                "timestamp": 1700000000000,
                "source": {"type": "user", "userId": "Uabc123def456"},
                "replyToken": "reply_token_xxx",
                "mode": "active",
            }
        ],
    }


@pytest.fixture
def line_image_event():
    return {
        "destination": "Uxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "image",
                    "id": "12345678901235",
                    "contentProvider": {"type": "line"},
                },
                "timestamp": 1700000001000,
                "source": {"type": "user", "userId": "Uabc123def456"},
                "replyToken": "reply_token_yyy",
                "mode": "active",
            }
        ],
    }


class TestLineVerifyWebhook:
    async def test_verify_valid_signature(self, line_adapter, line_account):
        body = b'{"events": []}'
        headers = {"x-line-signature": _make_line_signature(body, CHANNEL_SECRET)}
        result = await line_adapter.verify_webhook(
            body, headers, secret=CHANNEL_SECRET
        )
        assert result is True

    async def test_verify_invalid_signature(self, line_adapter, line_account):
        body = b'{"events": []}'
        headers = {"x-line-signature": "invalid_base64_sig=="}
        result = await line_adapter.verify_webhook(
            body, headers, secret=CHANNEL_SECRET
        )
        assert result is False

    async def test_verify_missing_header(self, line_adapter, line_account):
        result = await line_adapter.verify_webhook(
            b"", {}, secret=CHANNEL_SECRET
        )
        assert result is False


class TestLineParseWebhook:
    async def test_parse_text_message(self, line_adapter, line_account, line_text_event):
        messages = await line_adapter.parse_webhook(line_account, line_text_event)

        assert len(messages) == 1
        msg = messages[0]
        assert isinstance(msg, StandardMessage)
        assert msg.messenger_type == "line"
        assert msg.messenger_user_id == "Uabc123def456"
        assert msg.messenger_message_id == "12345678901234"
        assert msg.content == "ボトックスの料金を教えてください"
        assert msg.content_type == "text"

    async def test_parse_image_message(self, line_adapter, line_account, line_image_event):
        messages = await line_adapter.parse_webhook(line_account, line_image_event)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.content_type == "image"
        assert msg.attachments[0]["message_id"] == "12345678901235"

    async def test_parse_empty_events(self, line_adapter, line_account):
        payload = {"destination": "Uxx", "events": []}
        messages = await line_adapter.parse_webhook(line_account, payload)
        assert messages == []

    async def test_parse_ignores_non_message_event(self, line_adapter, line_account):
        payload = {
            "destination": "Uxx",
            "events": [
                {
                    "type": "follow",
                    "timestamp": 1700000000000,
                    "source": {"type": "user", "userId": "U123"},
                    "replyToken": "rt",
                }
            ],
        }
        messages = await line_adapter.parse_webhook(line_account, payload)
        assert messages == []


class TestLineSendMessage:
    async def test_send_push_message(self, line_adapter, line_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch("app.messenger.line.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            msg_id = await line_adapter.send_message(
                line_account, "Uabc123def456", "こんにちは！"
            )

        assert msg_id != ""
        call_args = mock_client.post.call_args
        assert "push" in call_args[0][0]
        body = call_args[1]["json"]
        assert body["to"] == "Uabc123def456"
        assert body["messages"][0]["text"] == "こんにちは！"


class TestLineFactoryRegistration:
    def test_line_registered(self):
        from app.messenger.factory import MessengerAdapterFactory

        supported = MessengerAdapterFactory.supported_types()
        assert "line" in supported
