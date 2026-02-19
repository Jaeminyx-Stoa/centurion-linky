"""Tests for AIResponseService — all LLM/messenger calls mocked."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.consultation_service import ConsultationResult
from app.ai.agents.escalation import EscalationLevel
from app.models.ab_test import ABTest, ABTestVariant
from app.models.ai_persona import AIPersona
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.cultural_profile import CulturalProfile
from app.models.customer import Customer
from app.models.message import Message
from app.models.messenger_account import MessengerAccount
from app.services.ai_response_service import AIResponseService


@pytest.fixture
async def clinic(db: AsyncSession) -> Clinic:
    c = Clinic(id=uuid.uuid4(), name="AI테스트의원", slug="ai-test-clinic")
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
        account_name="test-bot",
        is_active=True,
        is_connected=True,
        credentials={"bot_token": "fake"},
    )
    db.add(ma)
    await db.commit()
    await db.refresh(ma)
    return ma


@pytest.fixture
async def customer(db: AsyncSession, clinic: Clinic) -> Customer:
    cust = Customer(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        messenger_type="telegram",
        messenger_user_id="user_123",
        language_code="ko",
        country_code="KR",
    )
    db.add(cust)
    await db.commit()
    await db.refresh(cust)
    return cust


@pytest.fixture
async def conversation(
    db: AsyncSession, clinic: Clinic, customer: Customer, messenger_account: MessengerAccount
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        customer_id=customer.id,
        messenger_account_id=messenger_account.id,
        status="active",
        ai_mode=True,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@pytest.fixture
async def incoming_message(
    db: AsyncSession, clinic: Clinic, conversation: Conversation, customer: Customer
) -> Message:
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        clinic_id=clinic.id,
        sender_type="customer",
        sender_id=customer.id,
        content="보톡스 가격 알려주세요",
        content_type="text",
        messenger_type="telegram",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@pytest.fixture
def mock_consultation_service():
    svc = AsyncMock()
    svc.consult = AsyncMock(
        return_value=ConsultationResult(
            response="보톡스는 부위별 10만원부터 시작합니다.",
            escalated=False,
            escalation_level=EscalationLevel.NONE,
        )
    )
    return svc


@pytest.fixture
def mock_adapter():
    adapter = AsyncMock()
    adapter.send_message = AsyncMock(return_value="sent_msg_123")
    adapter.send_typing_indicator = AsyncMock()
    return adapter


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_ai_mode_off_skips(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service,
):
    """When ai_mode is False, generate_response should return None."""
    conversation.ai_mode = False
    await db.commit()

    svc = AIResponseService(db, mock_consultation_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is None
    mock_consultation_service.consult.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_normal_response_flow(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Normal flow should consult, save message, send via messenger, broadcast."""
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    assert result.sender_type == "ai"
    assert "보톡스" in result.content
    mock_consultation_service.consult.assert_called_once()
    mock_adapter.send_message.assert_called_once()
    assert mock_manager.broadcast_to_clinic.call_count >= 1


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_escalation_flow(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_adapter,
):
    """Escalation should turn off ai_mode and send escalation alert."""
    esc_service = AsyncMock()
    esc_service.consult = AsyncMock(
        return_value=ConsultationResult(
            response="전문 상담사가 곧 연결됩니다.",
            escalated=True,
            escalation_level=EscalationLevel.ESCALATE,
        )
    )
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, esc_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    # Verify escalation side effects
    await db.refresh(conversation)
    assert conversation.ai_mode is False
    assert conversation.status == "waiting"

    # Check escalation alert broadcast
    calls = mock_manager.broadcast_to_clinic.call_args_list
    escalation_calls = [c for c in calls if c[0][1].get("type") == "escalation_alert"]
    assert len(escalation_calls) >= 1


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_first_message_includes_greeting_and_disclosure(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """First AI message should include time greeting and AI disclosure."""
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    # Korean greeting patterns
    assert any(
        g in result.content
        for g in ["좋은 아침", "안녕하세요", "좋은 저녁", "늦은 시간"]
    )
    # AI disclosure
    assert "AI 상담사" in result.content


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_subsequent_message_no_greeting(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Subsequent AI messages should not include greeting/disclosure."""
    # Add an existing AI message
    existing_ai = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        clinic_id=clinic.id,
        sender_type="ai",
        content="이전 응답입니다.",
        content_type="text",
        messenger_type="telegram",
    )
    db.add(existing_ai)
    await db.commit()

    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    # Should NOT have disclosure prefix on subsequent messages
    assert not result.content.startswith("좋은")
    assert not result.content.startswith("안녕하세요")


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_non_korean_triggers_translation(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Non-Korean customer should trigger translation chain."""
    customer.language_code = "ja"
    await db.commit()

    mock_translation = AsyncMock()
    mock_translation.translate_incoming = AsyncMock(
        return_value=MagicMock(
            translated_text="ボトックスの価格を教えてください",
            skipped=False,
        )
    )
    mock_translation.translate_outgoing = AsyncMock(
        return_value=MagicMock(
            translated_text="ボトックスは10万ウォンからです。",
            skipped=False,
        )
    )

    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service, translation_chain=mock_translation)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    mock_translation.translate_incoming.assert_called_once()
    mock_translation.translate_outgoing.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_korean_skips_translation(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Korean customer should not trigger translation."""
    mock_factory.get_adapter.return_value = mock_adapter

    mock_translation = AsyncMock()

    svc = AIResponseService(db, mock_consultation_service, translation_chain=mock_translation)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    mock_translation.translate_incoming.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_satisfaction_updated(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Satisfaction score should be updated after AI response."""
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    await svc.generate_response(incoming_message.id, conversation.id)
    await db.flush()

    # Re-fetch from DB since the service may hold a different object reference
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation.id)
    )
    refreshed = result.scalar_one()
    assert refreshed.satisfaction_score is not None
    assert refreshed.satisfaction_level is not None


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_consultation_failure_no_crash(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_adapter,
):
    """If consultation raises, generate_response should return None without crashing."""
    failing_service = AsyncMock()
    failing_service.consult = AsyncMock(side_effect=Exception("LLM error"))
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, failing_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is None


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_cultural_profile_loaded(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Cultural profile should be loaded and passed to consultation."""
    profile = CulturalProfile(
        id=uuid.uuid4(),
        country_code="KR",
        country_name="대한민국",
        language_code="ko",
        style_prompt="존댓말 사용",
        emoji_level="medium",
        formality_level="polite",
    )
    db.add(profile)
    await db.commit()

    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    await svc.generate_response(incoming_message.id, conversation.id)

    call_args = mock_consultation_service.consult.call_args
    assert call_args.kwargs["cultural_profile"]["country_name"] == "대한민국"


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_persona_loaded(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """AI persona should be loaded and passed to consultation."""
    persona = AIPersona(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        name="미소",
        personality="밝고 친절한 상담사",
        is_default=True,
        is_active=True,
    )
    db.add(persona)
    await db.commit()

    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    await svc.generate_response(incoming_message.id, conversation.id)

    call_args = mock_consultation_service.consult.call_args
    assert call_args.kwargs["persona"]["name"] == "미소"


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_default_persona_fallback(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Without a configured persona, default values should be used."""
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    await svc.generate_response(incoming_message.id, conversation.id)

    call_args = mock_consultation_service.consult.call_args
    assert call_args.kwargs["persona"]["name"] == "상담사"


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_websocket_broadcast_format(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """WebSocket broadcast should use new_message type with correct format."""
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    await svc.generate_response(incoming_message.id, conversation.id)

    # Find the new_message broadcast call
    calls = mock_manager.broadcast_to_clinic.call_args_list
    new_msg_calls = [c for c in calls if c[0][1].get("type") == "new_message"]
    assert len(new_msg_calls) >= 1

    data = new_msg_calls[0][0][1]
    assert data["type"] == "new_message"
    assert "conversation_id" in data
    assert "message" in data
    assert data["message"]["sender_type"] == "ai"


# --- A/B Test Integration Tests ---


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_ab_test_variant_applied(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Active A/B test should select a variant and apply persona override."""
    ab_test = ABTest(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        name="Greeting Test",
        test_type="greeting",
        is_active=True,
        status="active",
    )
    db.add(ab_test)
    await db.flush()

    variant = ABTestVariant(
        id=uuid.uuid4(),
        ab_test_id=ab_test.id,
        name="Variant A",
        config={"personality": "매우 밝고 활기찬 상담사"},
        weight=100,
    )
    db.add(variant)
    await db.commit()

    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    # Persona personality should have been overridden by variant config
    call_args = mock_consultation_service.consult.call_args
    assert call_args.kwargs["persona"]["personality"] == "매우 밝고 활기찬 상담사"


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_no_active_ab_test_no_override(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """Without active A/B tests, persona should not be overridden."""
    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    result = await svc.generate_response(incoming_message.id, conversation.id)

    assert result is not None
    call_args = mock_consultation_service.consult.call_args
    assert call_args.kwargs["persona"]["name"] == "상담사"


@pytest.mark.asyncio
@patch("app.services.ai_response_service.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.ai_response_service.MessengerAdapterFactory")
@patch("app.services.ai_response_service.manager", new_callable=AsyncMock)
async def test_ab_test_outcome_recorded(
    mock_manager, mock_factory, mock_sleep,
    db, clinic, customer, messenger_account, conversation, incoming_message,
    mock_consultation_service, mock_adapter,
):
    """A/B test outcome should be recorded after AI response."""
    from app.models.ab_test import ABTestResult

    ab_test = ABTest(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        name="Sales Test",
        test_type="sales_strategy",
        is_active=True,
        status="active",
    )
    db.add(ab_test)
    await db.flush()

    variant = ABTestVariant(
        id=uuid.uuid4(),
        ab_test_id=ab_test.id,
        name="Control",
        config={},
        weight=100,
    )
    db.add(variant)
    await db.commit()

    mock_factory.get_adapter.return_value = mock_adapter

    svc = AIResponseService(db, mock_consultation_service)
    await svc.generate_response(incoming_message.id, conversation.id)
    await db.commit()

    # Check that an ABTestResult was recorded
    from sqlalchemy import select
    result = await db.execute(
        select(ABTestResult).where(ABTestResult.ab_test_id == ab_test.id)
    )
    outcomes = result.scalars().all()
    assert len(outcomes) >= 1
    assert outcomes[0].variant_id == variant.id
