"""Tests for AI message feedback API."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def feedback_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="피드백테스트의원", slug="feedback-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def feedback_customer(db: AsyncSession, feedback_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=feedback_clinic.id,
        messenger_type="telegram",
        messenger_user_id="fb-cust-1",
        name="Test Customer",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def feedback_account(db: AsyncSession, feedback_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=feedback_clinic.id,
        messenger_type="telegram",
        account_name="feedback-bot",
        credentials={"bot_token": "tok"},
        is_active=True,
        is_connected=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def feedback_conversation(
    db: AsyncSession,
    feedback_clinic: Clinic,
    feedback_customer: Customer,
    feedback_account: MessengerAccount,
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=feedback_clinic.id,
        customer_id=feedback_customer.id,
        messenger_account_id=feedback_account.id,
        status="active",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def ai_message(
    db: AsyncSession,
    feedback_clinic: Clinic,
    feedback_conversation: Conversation,
) -> Message:
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=feedback_conversation.id,
        clinic_id=feedback_clinic.id,
        sender_type="ai",
        content="AI response",
        content_type="text",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@pytest_asyncio.fixture
async def customer_message(
    db: AsyncSession,
    feedback_clinic: Clinic,
    feedback_conversation: Conversation,
) -> Message:
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=feedback_conversation.id,
        clinic_id=feedback_clinic.id,
        sender_type="customer",
        content="Hello",
        content_type="text",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


class TestMessageFeedback:
    @pytest.mark.asyncio
    async def test_submit_feedback_up(
        self, client, auth_headers, feedback_conversation, ai_message, db
    ):
        """Should store thumbs up feedback in ai_metadata."""
        response = client.post(
            f"/api/v1/conversations/{feedback_conversation.id}/messages/{ai_message.id}/feedback",
            json={"rating": "up"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["feedback"]["rating"] == "up"

    @pytest.mark.asyncio
    async def test_submit_feedback_with_note(
        self, client, auth_headers, feedback_conversation, ai_message
    ):
        """Should store feedback with optional note."""
        response = client.post(
            f"/api/v1/conversations/{feedback_conversation.id}/messages/{ai_message.id}/feedback",
            json={"rating": "down", "note": "Not relevant"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["feedback"]["rating"] == "down"
        assert data["feedback"]["note"] == "Not relevant"

    @pytest.mark.asyncio
    async def test_overwrite_existing_feedback(
        self, client, auth_headers, feedback_conversation, ai_message
    ):
        """Submitting feedback again should overwrite previous."""
        client.post(
            f"/api/v1/conversations/{feedback_conversation.id}/messages/{ai_message.id}/feedback",
            json={"rating": "up"},
            headers=auth_headers,
        )
        response = client.post(
            f"/api/v1/conversations/{feedback_conversation.id}/messages/{ai_message.id}/feedback",
            json={"rating": "down"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["feedback"]["rating"] == "down"

    @pytest.mark.asyncio
    async def test_feedback_on_customer_message_rejected(
        self, client, auth_headers, feedback_conversation, customer_message
    ):
        """Feedback should only be allowed on AI messages."""
        response = client.post(
            f"/api/v1/conversations/{feedback_conversation.id}/messages/{customer_message.id}/feedback",
            json={"rating": "up"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_feedback_message_not_found(
        self, client, auth_headers, feedback_conversation
    ):
        """Should return 404 for nonexistent message."""
        response = client.post(
            f"/api/v1/conversations/{feedback_conversation.id}/messages/{uuid.uuid4()}/feedback",
            json={"rating": "up"},
            headers=auth_headers,
        )
        assert response.status_code == 404
