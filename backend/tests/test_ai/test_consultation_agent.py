"""Tests for ConsultationAgent — agent with tool-calling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.agents.consultation_agent import ConsultationAgent


@pytest.mark.asyncio
async def test_agent_invokes_executor():
    """Agent should delegate to AgentExecutor and return output."""
    mock_executor = AsyncMock()
    mock_executor.ainvoke.return_value = {"output": "보톡스는 주름 개선 시술입니다."}

    agent = ConsultationAgent.__new__(ConsultationAgent)
    agent.executor = mock_executor

    result = await agent.ainvoke(
        input="보톡스가 뭔가요?",
        chat_history=[],
        persona_name="미소",
        persona_personality="친절한 상담사",
        rag_results="[FAQ]\nQ: 보톡스란?\nA: 주름 개선 시술",
        clinic_manual="",
        language_code="ko",
        cultural_context="",
    )

    assert result == "보톡스는 주름 개선 시술입니다."
    mock_executor.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_consultation_service_agent_fallback():
    """ConsultationService should fall back to chain when agent fails."""
    from app.ai.agents.consultation_service import ConsultationService, ConsultationResult
    from app.ai.agents.escalation import EscalationLevel

    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = "체인 응답입니다."

    mock_detector = AsyncMock()
    mock_detector.detect.return_value = EscalationLevel.NONE

    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = Exception("Agent error")

    service = ConsultationService(
        response_chain=mock_chain,
        escalation_detector=mock_detector,
        agent=mock_agent,
    )

    import uuid
    result = await service.consult(
        query="보톡스 가격",
        conversation_id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        rag_results="",
        clinic_manual="",
        country_code="KR",
        language_code="ko",
        cultural_profile={},
        persona={"name": "미소", "personality": "친절"},
        conversation_history="",
        sales_context={},
    )

    assert isinstance(result, ConsultationResult)
    assert result.response == "체인 응답입니다."
    assert not result.escalated


@pytest.mark.asyncio
async def test_consultation_service_uses_agent():
    """ConsultationService should use agent when available and working."""
    from app.ai.agents.consultation_service import ConsultationService
    from app.ai.agents.escalation import EscalationLevel

    mock_chain = AsyncMock()
    mock_detector = AsyncMock()
    mock_detector.detect.return_value = EscalationLevel.NONE

    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = "에이전트 응답입니다."

    service = ConsultationService(
        response_chain=mock_chain,
        escalation_detector=mock_detector,
        agent=mock_agent,
    )

    import uuid
    result = await service.consult(
        query="예약하고 싶어요",
        conversation_id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        rag_results="",
        clinic_manual="",
        country_code="KR",
        language_code="ko",
        cultural_profile={"style_prompt": ""},
        persona={"name": "미소", "personality": "친절"},
        conversation_history="",
        sales_context={},
    )

    assert result.response == "에이전트 응답입니다."
    mock_chain.ainvoke.assert_not_called()
