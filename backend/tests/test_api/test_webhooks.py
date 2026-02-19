"""Tests for messenger webhook endpoints (Meta, LINE, KakaoTalk)."""

import hashlib
import hmac
import base64
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.messenger_account import MessengerAccount


APP_SECRET = "meta_test_secret_123"
LINE_SECRET = "line_test_secret_456"
KAKAO_TOKEN = "kakao_verify_token_789"


@pytest_asyncio.fixture
async def wh_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="웹훅의원", slug="wh-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def ig_account(db: AsyncSession, wh_clinic: Clinic) -> MessengerAccount:
    acct = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=wh_clinic.id,
        messenger_type="instagram",
        account_name="clinic_ig",
        credentials={
            "page_access_token": "EAAxx",
            "app_secret": APP_SECRET,
        },
        webhook_secret="ig_verify_token",
        is_active=True,
        is_connected=True,
    )
    db.add(acct)
    await db.commit()
    await db.refresh(acct)
    return acct


@pytest_asyncio.fixture
async def line_account(db: AsyncSession, wh_clinic: Clinic) -> MessengerAccount:
    acct = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=wh_clinic.id,
        messenger_type="line",
        account_name="clinic_line",
        credentials={
            "channel_access_token": "line_token_xx",
            "channel_secret": LINE_SECRET,
        },
        webhook_secret=LINE_SECRET,
        is_active=True,
        is_connected=True,
    )
    db.add(acct)
    await db.commit()
    await db.refresh(acct)
    return acct


@pytest_asyncio.fixture
async def kakao_account(db: AsyncSession, wh_clinic: Clinic) -> MessengerAccount:
    acct = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=wh_clinic.id,
        messenger_type="kakao",
        account_name="clinic_kakao",
        credentials={
            "app_key": "kakao_xx",
            "bot_id": "bot_1",
            "api_key": "api_xx",
        },
        webhook_secret=KAKAO_TOKEN,
        is_active=True,
        is_connected=True,
    )
    db.add(acct)
    await db.commit()
    await db.refresh(acct)
    return acct


class TestMetaWebhookVerification:
    """Test GET /api/webhooks/meta/{account_id} for Meta verification."""

    @pytest.mark.asyncio
    async def test_verify_valid_token(
        self, client: AsyncClient, ig_account: MessengerAccount
    ):
        resp = await client.get(
            f"/api/webhooks/meta/{ig_account.id}",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "ig_verify_token",
                "hub.challenge": "1158201444",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "1158201444"

    @pytest.mark.asyncio
    async def test_verify_invalid_token(
        self, client: AsyncClient, ig_account: MessengerAccount
    ):
        resp = await client.get(
            f"/api/webhooks/meta/{ig_account.id}",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "12345",
            },
        )
        assert resp.status_code == 403


class TestMetaWebhookPost:
    """Test POST /api/webhooks/meta/{account_id}."""

    @pytest.mark.asyncio
    @patch("app.api.webhooks.meta.broadcast_incoming_message", new_callable=AsyncMock)
    @patch("app.api.webhooks.meta.process_ai_response_background", new_callable=AsyncMock)
    async def test_post_valid_ig_message(
        self, mock_ai_bg, mock_broadcast, client: AsyncClient, ig_account: MessengerAccount
    ):
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": "123",
                    "time": 1700000000,
                    "messaging": [
                        {
                            "sender": {"id": "user1"},
                            "recipient": {"id": "page1"},
                            "timestamp": 1700000000000,
                            "message": {"mid": "m_1", "text": "Hello"},
                        }
                    ],
                }
            ],
        }
        import json

        body = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(
            APP_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()

        resp = await client.post(
            f"/api/webhooks/meta/{ig_account.id}",
            content=body,
            headers={
                "x-hub-signature-256": sig,
                "content-type": "application/json",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_post_invalid_signature(
        self, client: AsyncClient, ig_account: MessengerAccount
    ):
        resp = await client.post(
            f"/api/webhooks/meta/{ig_account.id}",
            json={"object": "instagram", "entry": []},
            headers={"x-hub-signature-256": "sha256=invalid"},
        )
        assert resp.status_code == 403


class TestLineWebhookPost:
    """Test POST /api/webhooks/line/{account_id}."""

    @pytest.mark.asyncio
    @patch("app.api.webhooks.line.broadcast_incoming_message", new_callable=AsyncMock)
    @patch("app.api.webhooks.line.process_ai_response_background", new_callable=AsyncMock)
    async def test_post_valid_line_message(
        self, mock_ai_bg, mock_broadcast, client: AsyncClient, line_account: MessengerAccount
    ):
        import json

        payload = {
            "destination": "Uxx",
            "events": [
                {
                    "type": "message",
                    "message": {"type": "text", "id": "123", "text": "こんにちは"},
                    "timestamp": 1700000000000,
                    "source": {"type": "user", "userId": "U123"},
                    "replyToken": "rt",
                    "mode": "active",
                }
            ],
        }
        body = json.dumps(payload).encode()
        sig = base64.b64encode(
            hmac.new(LINE_SECRET.encode(), body, hashlib.sha256).digest()
        ).decode()

        resp = await client.post(
            f"/api/webhooks/line/{line_account.id}",
            content=body,
            headers={
                "x-line-signature": sig,
                "content-type": "application/json",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_post_invalid_line_signature(
        self, client: AsyncClient, line_account: MessengerAccount
    ):
        resp = await client.post(
            f"/api/webhooks/line/{line_account.id}",
            json={"events": []},
            headers={"x-line-signature": "invalid=="},
        )
        assert resp.status_code == 403


class TestKakaoWebhookPost:
    """Test POST /api/webhooks/kakao/{account_id}."""

    @pytest.mark.asyncio
    @patch("app.api.webhooks.kakao.broadcast_incoming_message", new_callable=AsyncMock)
    @patch("app.api.webhooks.kakao.process_ai_response_background", new_callable=AsyncMock)
    async def test_post_valid_kakao_message(
        self, mock_ai_bg, mock_broadcast, client: AsyncClient, kakao_account: MessengerAccount
    ):
        payload = {
            "userRequest": {
                "timezone": "Asia/Seoul",
                "block": {"id": "b1", "name": "default"},
                "utterance": "안녕하세요",
                "user": {"id": "kuser1", "type": "botUserKey", "properties": {}},
            },
            "bot": {"id": "bot_1", "name": "test"},
            "intent": {"id": "i1", "name": "default"},
            "action": {"name": "a1", "params": {}},
        }

        resp = await client.post(
            f"/api/webhooks/kakao/{kakao_account.id}",
            json=payload,
            headers={"x-kakao-bot-verification": KAKAO_TOKEN},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_post_invalid_kakao_token(
        self, client: AsyncClient, kakao_account: MessengerAccount
    ):
        resp = await client.post(
            f"/api/webhooks/kakao/{kakao_account.id}",
            json={"userRequest": {"utterance": "hi", "user": {"id": "x"}}},
            headers={"x-kakao-bot-verification": "wrong"},
        )
        assert resp.status_code == 403
