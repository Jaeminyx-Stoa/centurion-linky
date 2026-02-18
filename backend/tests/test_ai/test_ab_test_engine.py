import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ab_test_engine import ABTestEngine
from app.models.ab_test import ABTest, ABTestVariant
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount


# --- Fixtures ---
@pytest_asyncio.fixture
async def ab_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="AB의원", slug="ab-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def ab_test(db: AsyncSession, ab_clinic: Clinic) -> ABTest:
    test = ABTest(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        name="인사말 테스트",
        test_type="greeting",
        status="active",
        is_active=True,
    )
    db.add(test)
    await db.flush()

    for name in ["A안", "B안"]:
        v = ABTestVariant(
            id=uuid.uuid4(),
            ab_test_id=test.id,
            name=name,
            config={"greeting": f"테스트 {name}"},
        )
        db.add(v)

    await db.commit()
    await db.refresh(test)
    return test


@pytest_asyncio.fixture
async def ab_conversation(
    db: AsyncSession, ab_clinic: Clinic
) -> Conversation:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        messenger_type="telegram",
        messenger_user_id="ab-tg-1",
    )
    db.add(customer)
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        messenger_type="telegram",
        account_name="ab-bot",
        credentials={"token": "test"},
        is_active=True,
    )
    db.add(account)
    await db.flush()

    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        customer_id=customer.id,
        messenger_account_id=account.id,
        status="active",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


# --- Tests ---
class TestSelectVariant:
    @pytest.mark.asyncio
    async def test_selects_variant(
        self, db: AsyncSession, ab_test: ABTest, ab_conversation: Conversation
    ):
        engine = ABTestEngine(db)
        variant = await engine.select_variant(ab_test.id, ab_conversation.id)
        assert variant is not None
        assert variant.ab_test_id == ab_test.id

    @pytest.mark.asyncio
    async def test_consistent_selection(
        self, db: AsyncSession, ab_test: ABTest, ab_conversation: Conversation
    ):
        engine = ABTestEngine(db)
        v1 = await engine.select_variant(ab_test.id, ab_conversation.id)
        v2 = await engine.select_variant(ab_test.id, ab_conversation.id)
        assert v1.id == v2.id

    @pytest.mark.asyncio
    async def test_inactive_test_returns_none(
        self, db: AsyncSession, ab_clinic: Clinic, ab_conversation: Conversation
    ):
        test = ABTest(
            id=uuid.uuid4(),
            clinic_id=ab_clinic.id,
            name="비활성 테스트",
            test_type="prompt",
            is_active=False,
        )
        db.add(test)
        await db.commit()

        engine = ABTestEngine(db)
        variant = await engine.select_variant(test.id, ab_conversation.id)
        assert variant is None


class TestRecordOutcome:
    @pytest.mark.asyncio
    async def test_record(
        self, db: AsyncSession, ab_test: ABTest, ab_conversation: Conversation
    ):
        engine = ABTestEngine(db)
        variant = await engine.select_variant(ab_test.id, ab_conversation.id)
        result = await engine.record_outcome(
            test_id=ab_test.id,
            variant_id=variant.id,
            conversation_id=ab_conversation.id,
            outcome="booked",
        )
        assert result.outcome == "booked"
        assert result.ab_test_id == ab_test.id

    @pytest.mark.asyncio
    async def test_record_with_data(
        self, db: AsyncSession, ab_test: ABTest, ab_conversation: Conversation
    ):
        engine = ABTestEngine(db)
        variant = await engine.select_variant(ab_test.id, ab_conversation.id)
        result = await engine.record_outcome(
            test_id=ab_test.id,
            variant_id=variant.id,
            conversation_id=ab_conversation.id,
            outcome="paid",
            outcome_data={"amount": 100000, "satisfaction": 85},
        )
        assert result.outcome_data["amount"] == 100000


class TestGetStats:
    @pytest.mark.asyncio
    async def test_empty_stats(self, db: AsyncSession, ab_test: ABTest):
        engine = ABTestEngine(db)
        stats = await engine.get_stats(ab_test.id)
        assert len(stats) == 2
        assert all(s["total_conversations"] == 0 for s in stats)

    @pytest.mark.asyncio
    async def test_stats_with_outcomes(
        self, db: AsyncSession, ab_test: ABTest, ab_conversation: Conversation
    ):
        engine = ABTestEngine(db)
        variant = await engine.select_variant(ab_test.id, ab_conversation.id)
        await engine.record_outcome(
            ab_test.id, variant.id, ab_conversation.id, "booked"
        )
        stats = await engine.get_stats(ab_test.id)
        total = sum(s["total_conversations"] for s in stats)
        assert total == 1
