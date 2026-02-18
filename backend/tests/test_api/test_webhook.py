import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clinic, MessengerAccount


@pytest.fixture
async def webhook_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="웹훅테스트의원",
        slug="webhook-test-clinic",
    )
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def telegram_account(db: AsyncSession, webhook_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=webhook_clinic.id,
        messenger_type="telegram",
        account_name="test_bot",
        credentials={"bot_token": "123456:ABC-DEF"},
        webhook_secret="test-secret",
        is_active=True,
        is_connected=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


class TestTelegramWebhook:
    """POST /api/webhooks/telegram/{account_id}"""

    async def test_webhook_processes_text_message(
        self, client: AsyncClient, telegram_account: MessengerAccount
    ):
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 42,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Yuko",
                    "language_code": "ja",
                },
                "chat": {"id": 987654321, "type": "private"},
                "date": 1700000000,
                "text": "ボトックスの料金を教えてください",
            },
        }

        response = await client.post(
            f"/api/webhooks/telegram/{telegram_account.id}",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_webhook_creates_customer_and_conversation(
        self, client: AsyncClient, telegram_account: MessengerAccount
    ):
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 42,
                "from": {"id": 111222333, "first_name": "Test"},
                "chat": {"id": 111222333, "type": "private"},
                "date": 1700000000,
                "text": "Hello",
            },
        }

        response = await client.post(
            f"/api/webhooks/telegram/{telegram_account.id}",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        )

        assert response.status_code == 200

        # Send a second message — should reuse customer and conversation
        payload["message"]["message_id"] = 43
        payload["message"]["text"] = "Second message"

        response2 = await client.post(
            f"/api/webhooks/telegram/{telegram_account.id}",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        )
        assert response2.status_code == 200

    async def test_webhook_rejects_invalid_secret(
        self, client: AsyncClient, telegram_account: MessengerAccount
    ):
        payload = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 1},
                "chat": {"id": 1, "type": "private"},
                "date": 1700000000,
                "text": "test",
            },
        }

        response = await client.post(
            f"/api/webhooks/telegram/{telegram_account.id}",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert response.status_code == 403

    async def test_webhook_rejects_unknown_account(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/webhooks/telegram/{fake_id}",
            json={"update_id": 1},
        )
        assert response.status_code == 404

    async def test_webhook_rejects_inactive_account(
        self, client: AsyncClient, db: AsyncSession, telegram_account: MessengerAccount
    ):
        telegram_account.is_active = False
        db.add(telegram_account)
        await db.commit()

        response = await client.post(
            f"/api/webhooks/telegram/{telegram_account.id}",
            json={"update_id": 1, "message": {"message_id": 1, "from": {"id": 1}, "chat": {"id": 1, "type": "private"}, "date": 1700000000, "text": "hi"}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        )
        assert response.status_code == 403
