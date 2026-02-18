"""Tests for KakaoTalk Channel API adapter."""

import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messenger.base import StandardMessage
from app.messenger.kakao import KakaoAdapter
from app.models.messenger_account import MessengerAccount


@pytest.fixture
def kakao_adapter():
    return KakaoAdapter()


@pytest.fixture
def kakao_account():
    return MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        messenger_type="kakao",
        account_name="clinic_kakao",
        credentials={
            "app_key": "kakao_app_key_xxx",
            "bot_id": "bot_123",
            "api_key": "kakao_api_key_yyy",
        },
        webhook_secret="kakao_verify_token",
    )


@pytest.fixture
def kakao_text_payload():
    """KakaoTalk Channel chatbot webhook payload (skill format)."""
    return {
        "intent": {"id": "intent_id", "name": "default"},
        "userRequest": {
            "timezone": "Asia/Seoul",
            "block": {"id": "block_id", "name": "default"},
            "utterance": "보톡스 가격 알려주세요",
            "user": {
                "id": "kakao_user_123",
                "type": "botUserKey",
                "properties": {},
            },
        },
        "bot": {"id": "bot_123", "name": "클리닉봇"},
        "action": {"name": "action_name", "params": {}},
    }


@pytest.fixture
def kakao_image_payload():
    return {
        "intent": {"id": "intent_id", "name": "default"},
        "userRequest": {
            "timezone": "Asia/Seoul",
            "block": {"id": "block_id", "name": "default"},
            "utterance": "사진",
            "user": {
                "id": "kakao_user_456",
                "type": "botUserKey",
                "properties": {
                    "plusfriendUserKey": "plus_friend_key",
                },
            },
            "params": {
                "media": {
                    "type": "image",
                    "url": "https://cdn.kakao.com/photo.jpg",
                }
            },
        },
        "bot": {"id": "bot_123", "name": "클리닉봇"},
        "action": {"name": "action_name", "params": {}},
    }


class TestKakaoVerifyWebhook:
    async def test_verify_with_matching_token(self, kakao_adapter, kakao_account):
        headers = {"x-kakao-bot-verification": "kakao_verify_token"}
        result = await kakao_adapter.verify_webhook(
            b"", headers, secret="kakao_verify_token"
        )
        assert result is True

    async def test_verify_with_wrong_token(self, kakao_adapter, kakao_account):
        headers = {"x-kakao-bot-verification": "wrong"}
        result = await kakao_adapter.verify_webhook(
            b"", headers, secret="kakao_verify_token"
        )
        assert result is False

    async def test_verify_missing_header(self, kakao_adapter, kakao_account):
        result = await kakao_adapter.verify_webhook(
            b"", {}, secret="kakao_verify_token"
        )
        assert result is False


class TestKakaoParseWebhook:
    async def test_parse_text_message(
        self, kakao_adapter, kakao_account, kakao_text_payload
    ):
        messages = await kakao_adapter.parse_webhook(kakao_account, kakao_text_payload)

        assert len(messages) == 1
        msg = messages[0]
        assert isinstance(msg, StandardMessage)
        assert msg.messenger_type == "kakao"
        assert msg.messenger_user_id == "kakao_user_123"
        assert msg.content == "보톡스 가격 알려주세요"
        assert msg.content_type == "text"

    async def test_parse_image_message(
        self, kakao_adapter, kakao_account, kakao_image_payload
    ):
        messages = await kakao_adapter.parse_webhook(kakao_account, kakao_image_payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.content_type == "image"
        assert msg.attachments[0]["url"] == "https://cdn.kakao.com/photo.jpg"

    async def test_parse_empty_payload(self, kakao_adapter, kakao_account):
        messages = await kakao_adapter.parse_webhook(kakao_account, {})
        assert messages == []


class TestKakaoSendMessage:
    async def test_send_text(self, kakao_adapter, kakao_account):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result_code": 0}

        with patch("app.messenger.kakao.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            msg_id = await kakao_adapter.send_message(
                kakao_account, "kakao_user_123", "안녕하세요!"
            )

        assert msg_id != ""
        mock_client.post.assert_called_once()


class TestKakaoFactoryRegistration:
    def test_kakao_registered(self):
        from app.messenger.factory import MessengerAdapterFactory

        supported = MessengerAdapterFactory.supported_types()
        assert "kakao" in supported
