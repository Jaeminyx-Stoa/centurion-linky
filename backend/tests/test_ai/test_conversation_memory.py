import uuid
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.conversation_memory import ConversationMemory
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.models.messenger_account import MessengerAccount


# --- Fixtures ---
@pytest_asyncio.fixture
async def mem_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="메모리의원", slug="mem-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def mem_customer(db: AsyncSession, mem_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=mem_clinic.id,
        messenger_type="telegram",
        messenger_user_id="mem-tg-1",
        name="메모리고객",
        display_name="메모리님",
        language_code="ko",
        timezone="Asia/Seoul",
        country_code="KR",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def mem_account(db: AsyncSession, mem_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=mem_clinic.id,
        messenger_type="telegram",
        account_name="mem-bot",
        credentials={"token": "test"},
        is_active=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def mem_conversation(
    db: AsyncSession,
    mem_clinic: Clinic,
    mem_customer: Customer,
    mem_account: MessengerAccount,
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=mem_clinic.id,
        customer_id=mem_customer.id,
        messenger_account_id=mem_account.id,
        status="active",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def mem_messages(
    db: AsyncSession,
    mem_clinic: Clinic,
    mem_conversation: Conversation,
) -> list[Message]:
    now = datetime.now(timezone.utc)
    msgs = []
    for i in range(5):
        m = Message(
            id=uuid.uuid4(),
            conversation_id=mem_conversation.id,
            clinic_id=mem_clinic.id,
            sender_type="customer" if i % 2 == 0 else "ai",
            content=f"메시지 {i + 1}번째입니다",
            created_at=now - timedelta(minutes=5 - i),
        )
        db.add(m)
        msgs.append(m)
    await db.commit()
    for m in msgs:
        await db.refresh(m)
    return msgs


@pytest_asyncio.fixture
async def mem_many_messages(
    db: AsyncSession,
    mem_clinic: Clinic,
    mem_conversation: Conversation,
) -> list[Message]:
    """Create 25 messages to test limit behavior."""
    now = datetime.now(timezone.utc)
    msgs = []
    for i in range(25):
        m = Message(
            id=uuid.uuid4(),
            conversation_id=mem_conversation.id,
            clinic_id=mem_clinic.id,
            sender_type="customer" if i % 2 == 0 else "ai",
            content=f"대화 {i + 1}번째 메시지",
            created_at=now - timedelta(minutes=25 - i),
        )
        db.add(m)
        msgs.append(m)
    await db.commit()
    for m in msgs:
        await db.refresh(m)
    return msgs


@pytest_asyncio.fixture
async def mem_booking(
    db: AsyncSession,
    mem_clinic: Clinic,
    mem_customer: Customer,
    mem_conversation: Conversation,
) -> Booking:
    from datetime import date, time

    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=mem_clinic.id,
        customer_id=mem_customer.id,
        conversation_id=mem_conversation.id,
        booking_date=date(2026, 4, 1),
        booking_time=time(14, 0),
        status="confirmed",
        total_amount=100000,
        currency="KRW",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


# --- Tests ---
class TestLoadRecentMessages:
    @pytest.mark.asyncio
    async def test_loads_messages(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert "recent_messages" in result
        assert len(result["recent_messages"]) == 5

    @pytest.mark.asyncio
    async def test_messages_ordered_chronologically(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        msgs = result["recent_messages"]
        for i in range(len(msgs) - 1):
            assert msgs[i]["created_at"] <= msgs[i + 1]["created_at"]

    @pytest.mark.asyncio
    async def test_limits_to_20_messages(
        self, db: AsyncSession, mem_conversation: Conversation, mem_many_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert len(result["recent_messages"]) == 20

    @pytest.mark.asyncio
    async def test_empty_conversation(
        self, db: AsyncSession, mem_conversation: Conversation
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert result["recent_messages"] == []

    @pytest.mark.asyncio
    async def test_message_dict_structure(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        msg = result["recent_messages"][0]
        assert "sender_type" in msg
        assert "content" in msg
        assert "created_at" in msg


class TestCustomerContext:
    @pytest.mark.asyncio
    async def test_includes_customer_context(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert "customer_context" in result
        ctx = result["customer_context"]
        assert ctx["display_name"] == "메모리님"
        assert ctx["language_code"] == "ko"
        assert ctx["country_code"] == "KR"

    @pytest.mark.asyncio
    async def test_includes_booking_count(
        self,
        db: AsyncSession,
        mem_conversation: Conversation,
        mem_messages: list[Message],
        mem_booking: Booking,
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        ctx = result["customer_context"]
        assert ctx["booking_count"] >= 1


class TestConversationSummary:
    @pytest.mark.asyncio
    async def test_includes_summary_field(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_returns_existing_summary(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        mem_conversation.summary = "보톡스 상담 진행 중"
        await db.commit()
        await db.refresh(mem_conversation)

        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert result["summary"] == "보톡스 상담 진행 중"

    @pytest.mark.asyncio
    async def test_summary_none_when_not_set(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert result["summary"] is None


class TestMessageCount:
    @pytest.mark.asyncio
    async def test_total_count_included(
        self, db: AsyncSession, mem_conversation: Conversation, mem_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert result["total_message_count"] == 5

    @pytest.mark.asyncio
    async def test_total_count_many(
        self, db: AsyncSession, mem_conversation: Conversation, mem_many_messages: list[Message]
    ):
        memory = ConversationMemory(db)
        result = await memory.load_memory(mem_conversation.id)
        assert result["total_message_count"] == 25
