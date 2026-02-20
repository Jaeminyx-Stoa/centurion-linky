"""Tests for CRM event execution task logic."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.crm_event import CRMEvent
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.tasks.crm_execution import _build_default_message, _execute_due_events


# --- Fixtures ---
@pytest_asyncio.fixture
async def crm_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="CRM테스트의원", slug="crm-exec-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def crm_account(db: AsyncSession, crm_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        messenger_type="telegram",
        account_name="crm-test-bot",
        credentials={"bot_token": "test-token"},
        is_active=True,
        is_connected=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def crm_customer(db: AsyncSession, crm_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        messenger_type="telegram",
        messenger_user_id="crm-tg-user-1",
        name="Test Customer",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def crm_conversation(
    db: AsyncSession,
    crm_clinic: Clinic,
    crm_customer: Customer,
    crm_account: MessengerAccount,
) -> Conversation:
    conversation = Conversation(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        customer_id=crm_customer.id,
        messenger_account_id=crm_account.id,
        status="active",
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@pytest_asyncio.fixture
async def crm_due_event(
    db: AsyncSession,
    crm_clinic: Clinic,
    crm_customer: Customer,
) -> CRMEvent:
    """A CRM event that is already past due."""
    event = CRMEvent(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        customer_id=crm_customer.id,
        event_type="receipt",
        scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        status="scheduled",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


# --- Tests ---
class TestBuildDefaultMessage:
    def test_receipt_message(self):
        msg = _build_default_message("receipt", "Alice")
        assert "Alice" in msg
        assert "payment" in msg.lower() or "thank" in msg.lower()

    def test_review_request(self):
        msg = _build_default_message("review_request", "Bob")
        assert "Bob" in msg
        assert "review" in msg.lower()

    def test_aftercare(self):
        msg = _build_default_message("aftercare", "Charlie")
        assert "Charlie" in msg
        assert "aftercare" in msg.lower() or "care" in msg.lower()

    def test_survey_messages(self):
        for survey_type in ("survey_1", "survey_2", "survey_3"):
            msg = _build_default_message(survey_type, "Diana")
            assert "Diana" in msg

    def test_revisit_reminder(self):
        msg = _build_default_message("revisit_reminder", "Eve")
        assert "Eve" in msg

    def test_unknown_type(self):
        msg = _build_default_message("unknown_event", "Frank")
        assert "Frank" in msg
        assert "clinic" in msg.lower()

    def test_none_name_uses_customer(self):
        msg = _build_default_message("receipt", None)
        assert "Customer" in msg


class TestExecuteDueEvents:
    @pytest.mark.asyncio
    async def test_no_due_events_returns_zero(self, db: AsyncSession):
        """When no events are due, returns sent=0 failed=0."""
        # Patch async_session_factory to use test DB
        with patch(
            "app.core.database.async_session_factory",
            return_value=db,
        ):
            # Create a mock context manager
            mock_session_cm = AsyncMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=db)
            mock_session_cm.__aexit__ = AsyncMock(return_value=False)

            with patch(
                "app.core.database.async_session_factory",
                return_value=mock_session_cm,
            ):
                result = await _execute_due_events()
                assert result["sent"] == 0
                assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_marks_failed_when_no_conversation(
        self,
        db: AsyncSession,
        crm_due_event: CRMEvent,
    ):
        """Events with no matching conversation are marked as failed."""
        # No conversation exists for the customer
        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=db)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.core.database.async_session_factory",
            return_value=mock_session_cm,
        ):
            result = await _execute_due_events()
            assert result["failed"] == 1
            assert result["sent"] == 0

            # Verify event is marked failed
            await db.refresh(crm_due_event)
            assert crm_due_event.status == "failed"

    @pytest.mark.asyncio
    async def test_sends_message_successfully(
        self,
        db: AsyncSession,
        crm_due_event: CRMEvent,
        crm_conversation: Conversation,
    ):
        """Due events with a conversation are sent via messenger adapter."""
        mock_adapter = AsyncMock()
        mock_adapter.send_message = AsyncMock(return_value="msg-123")

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=db)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.core.database.async_session_factory",
                return_value=mock_session_cm,
            ),
            patch(
                "app.messenger.factory.MessengerAdapterFactory"
            ) as mock_factory,
        ):
            mock_factory.get_adapter.return_value = mock_adapter

            result = await _execute_due_events()
            assert result["sent"] == 1
            assert result["failed"] == 0

            # Verify adapter was called
            mock_adapter.send_message.assert_called_once()

            # Verify event is marked sent
            await db.refresh(crm_due_event)
            assert crm_due_event.status == "sent"
            assert crm_due_event.executed_at is not None

    @pytest.mark.asyncio
    async def test_marks_failed_on_send_error(
        self,
        db: AsyncSession,
        crm_due_event: CRMEvent,
        crm_conversation: Conversation,
    ):
        """Events that fail to send are marked as failed."""
        mock_adapter = AsyncMock()
        mock_adapter.send_message = AsyncMock(
            side_effect=Exception("Telegram API error")
        )

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=db)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.core.database.async_session_factory",
                return_value=mock_session_cm,
            ),
            patch(
                "app.messenger.factory.MessengerAdapterFactory"
            ) as mock_factory,
        ):
            mock_factory.get_adapter.return_value = mock_adapter

            result = await _execute_due_events()
            assert result["sent"] == 0
            assert result["failed"] == 1

            # Verify event is marked failed
            await db.refresh(crm_due_event)
            assert crm_due_event.status == "failed"

    @pytest.mark.asyncio
    async def test_uses_custom_message_content(
        self,
        db: AsyncSession,
        crm_clinic: Clinic,
        crm_customer: Customer,
        crm_conversation: Conversation,
    ):
        """Events with message_content use that instead of default."""
        custom_msg = "Custom CRM message for you!"
        event = CRMEvent(
            id=uuid.uuid4(),
            clinic_id=crm_clinic.id,
            customer_id=crm_customer.id,
            event_type="receipt",
            scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            status="scheduled",
            message_content=custom_msg,
        )
        db.add(event)
        await db.commit()

        mock_adapter = AsyncMock()
        mock_adapter.send_message = AsyncMock(return_value="msg-456")

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=db)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.core.database.async_session_factory",
                return_value=mock_session_cm,
            ),
            patch(
                "app.messenger.factory.MessengerAdapterFactory"
            ) as mock_factory,
        ):
            mock_factory.get_adapter.return_value = mock_adapter

            await _execute_due_events()

            # Verify custom message was sent
            call_kwargs = mock_adapter.send_message.call_args
            assert call_kwargs[1]["text"] == custom_msg or call_kwargs.kwargs["text"] == custom_msg
