import hashlib
import hmac
import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messenger.base import StandardMessage
from app.messenger.telegram import TelegramAdapter
from app.models.messenger_account import MessengerAccount


@pytest.fixture
def telegram_adapter():
    return TelegramAdapter()


@pytest.fixture
def mock_account():
    """Create a mock MessengerAccount for Telegram."""
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        messenger_type="telegram",
        account_name="test_bot",
        credentials={"bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"},
        webhook_secret="test-webhook-secret",
    )
    return account


@pytest.fixture
def telegram_text_update():
    """A standard Telegram text message update."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 42,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "Yuko",
                "last_name": "Tanaka",
                "language_code": "ja",
            },
            "chat": {"id": 987654321, "type": "private"},
            "date": 1700000000,
            "text": "ボトックスの価格を教えてください",
        },
    }


@pytest.fixture
def telegram_photo_update():
    """A Telegram photo message update."""
    return {
        "update_id": 123456790,
        "message": {
            "message_id": 43,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "Yuko",
            },
            "chat": {"id": 987654321, "type": "private"},
            "date": 1700000001,
            "photo": [
                {"file_id": "small_id", "width": 90, "height": 90},
                {"file_id": "medium_id", "width": 320, "height": 320},
                {"file_id": "large_id", "width": 800, "height": 800},
            ],
            "caption": "이 사진 참고해주세요",
        },
    }


class TestTelegramParseWebhook:
    """Test parsing Telegram webhook payloads into StandardMessage."""

    async def test_parse_text_message(
        self, telegram_adapter, mock_account, telegram_text_update
    ):
        messages = await telegram_adapter.parse_webhook(mock_account, telegram_text_update)

        assert len(messages) == 1
        msg = messages[0]
        assert isinstance(msg, StandardMessage)
        assert msg.messenger_type == "telegram"
        assert msg.messenger_message_id == "42"
        assert msg.messenger_user_id == "987654321"
        assert msg.account_id == mock_account.id
        assert msg.clinic_id == mock_account.clinic_id
        assert msg.content == "ボトックスの価格を教えてください"
        assert msg.content_type == "text"
        assert msg.raw_data == telegram_text_update

    async def test_parse_photo_message(
        self, telegram_adapter, mock_account, telegram_photo_update
    ):
        messages = await telegram_adapter.parse_webhook(mock_account, telegram_photo_update)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.content_type == "image"
        assert msg.content == "이 사진 참고해주세요"
        assert len(msg.attachments) == 1
        assert msg.attachments[0]["file_id"] == "large_id"

    async def test_parse_ignores_non_message_update(
        self, telegram_adapter, mock_account
    ):
        # Telegram sends various update types (edited_message, callback_query, etc.)
        update = {"update_id": 123, "edited_message": {"message_id": 1}}
        messages = await telegram_adapter.parse_webhook(mock_account, update)
        assert messages == []

    async def test_parse_photo_without_caption(
        self, telegram_adapter, mock_account, telegram_photo_update
    ):
        del telegram_photo_update["message"]["caption"]
        messages = await telegram_adapter.parse_webhook(mock_account, telegram_photo_update)

        msg = messages[0]
        assert msg.content == ""
        assert msg.content_type == "image"


class TestTelegramVerifyWebhook:
    """Test Telegram webhook signature verification."""

    async def test_verify_valid_secret_token(self, telegram_adapter, mock_account):
        headers = {"x-telegram-bot-api-secret-token": "test-webhook-secret"}
        result = await telegram_adapter.verify_webhook(
            b"", headers, secret=mock_account.webhook_secret
        )
        assert result is True

    async def test_verify_invalid_secret_token(self, telegram_adapter, mock_account):
        headers = {"x-telegram-bot-api-secret-token": "wrong-secret"}
        result = await telegram_adapter.verify_webhook(
            b"", headers, secret=mock_account.webhook_secret
        )
        assert result is False

    async def test_verify_missing_secret_token(self, telegram_adapter, mock_account):
        headers = {}
        result = await telegram_adapter.verify_webhook(
            b"", headers, secret=mock_account.webhook_secret
        )
        assert result is False


class TestTelegramSendMessage:
    """Test sending messages via Telegram Bot API."""

    async def test_send_text_message(self, telegram_adapter, mock_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "result": {"message_id": 100},
        }

        with patch("app.messenger.telegram.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            message_id = await telegram_adapter.send_message(
                mock_account, "987654321", "안녕하세요!"
            )

        assert message_id == "100"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "sendMessage" in call_args[0][0]
        assert call_args[1]["json"]["chat_id"] == "987654321"
        assert call_args[1]["json"]["text"] == "안녕하세요!"

    async def test_send_typing_indicator(self, telegram_adapter, mock_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        with patch("app.messenger.telegram.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await telegram_adapter.send_typing_indicator(mock_account, "987654321")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "sendChatAction" in call_args[0][0]


class TestTelegramGetUserProfile:
    """Test fetching user profile from Telegram."""

    async def test_get_user_profile(self, telegram_adapter, mock_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "result": {
                "id": 987654321,
                "first_name": "Yuko",
                "last_name": "Tanaka",
                "type": "private",
            },
        }

        with patch("app.messenger.telegram.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            profile = await telegram_adapter.get_user_profile(mock_account, "987654321")

        assert profile["first_name"] == "Yuko"
        assert profile["last_name"] == "Tanaka"
