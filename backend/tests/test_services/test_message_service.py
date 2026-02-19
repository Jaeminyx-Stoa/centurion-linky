"""Tests for MessageService — ProcessingResult return type."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.messenger.base import StandardMessage
from app.models.clinic import Clinic
from app.models.messenger_account import MessengerAccount
from app.services.message_service import MessageService, ProcessingResult


@pytest.fixture
async def clinic(db: AsyncSession) -> Clinic:
    c = Clinic(id=uuid.uuid4(), name="MSG테스트", slug="msg-test")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@pytest.fixture
async def messenger_account(db: AsyncSession, clinic: Clinic) -> MessengerAccount:
    ma = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        messenger_type="telegram",
        account_name="test",
        is_active=True,
        credentials={},
    )
    db.add(ma)
    await db.commit()
    await db.refresh(ma)
    return ma


@pytest.fixture
def make_std_msg(clinic, messenger_account):
    def _factory(**overrides):
        defaults = {
            "messenger_type": "telegram",
            "messenger_message_id": str(uuid.uuid4()),
            "messenger_user_id": "user_abc",
            "account_id": messenger_account.id,
            "clinic_id": clinic.id,
            "content": "테스트 메시지",
            "content_type": "text",
        }
        defaults.update(overrides)
        return StandardMessage(**defaults)
    return _factory


@pytest.mark.asyncio
async def test_process_incoming_returns_processing_result(db, make_std_msg):
    """process_incoming should return a ProcessingResult dataclass."""
    svc = MessageService(db)
    result = await svc.process_incoming(make_std_msg())

    assert isinstance(result, ProcessingResult)
    assert result.message is not None
    assert result.conversation is not None
    assert result.customer is not None


@pytest.mark.asyncio
async def test_first_conversation_is_new(db, make_std_msg):
    """First message from a customer should create a new conversation."""
    svc = MessageService(db)
    result = await svc.process_incoming(make_std_msg())

    assert result.is_new_conversation is True


@pytest.mark.asyncio
async def test_existing_conversation_not_new(db, make_std_msg):
    """Second message from same customer should reuse existing conversation."""
    svc = MessageService(db)
    result1 = await svc.process_incoming(make_std_msg(messenger_user_id="same_user"))
    await db.commit()

    result2 = await svc.process_incoming(make_std_msg(messenger_user_id="same_user"))

    assert result2.is_new_conversation is False
    assert result1.conversation.id == result2.conversation.id
