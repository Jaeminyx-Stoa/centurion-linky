import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ai.agents.consultation_service import ConsultationService, ConsultationResult
from app.ai.agents.escalation import EscalationLevel


@pytest.fixture
def mock_response_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = "ボトックスについてご案内いたします。初回限定キャンペーン実施中です😊"
    return mock


@pytest.fixture
def mock_escalation_detector():
    mock = AsyncMock()
    mock.detect.return_value = EscalationLevel.NONE
    return mock


@pytest.fixture
def service(mock_response_chain, mock_escalation_detector):
    return ConsultationService(
        response_chain=mock_response_chain,
        escalation_detector=mock_escalation_detector,
    )


@pytest.fixture
def consultation_context():
    return {
        "query": "보톡스에 대해 알려주세요",
        "conversation_id": uuid.uuid4(),
        "clinic_id": uuid.uuid4(),
        "rag_results": "보톡스 관련 정보",
        "clinic_manual": "앨러간 보톡스 사용",
        "country_code": "JP",
        "language_code": "ja",
        "cultural_profile": {
            "country_code": "JP",
            "country_name": "일본",
            "language_code": "ja",
            "style_prompt": "정중한 일본어",
            "preferred_expressions": [],
            "avoided_expressions": [],
            "emoji_level": "medium",
            "formality_level": "formal",
        },
        "persona": {"name": "미소", "personality": "밝고 친근한 상담사"},
        "conversation_history": "",
        "sales_context": {
            "top_procedures": ["보톡스"],
            "active_events": [],
            "cross_sell_options": [],
        },
    }


class TestConsultationService:
    async def test_normal_consultation_returns_ai_response(
        self, service, consultation_context, mock_response_chain
    ):
        result = await service.consult(**consultation_context)

        assert isinstance(result, ConsultationResult)
        assert result.response is not None
        assert result.escalated is False
        assert result.escalation_level == EscalationLevel.NONE
        mock_response_chain.ainvoke.assert_called_once()

    async def test_escalation_stops_ai_response(
        self, mock_response_chain, consultation_context
    ):
        mock_escalation = AsyncMock()
        mock_escalation.detect.return_value = EscalationLevel.ESCALATE

        service = ConsultationService(
            response_chain=mock_response_chain,
            escalation_detector=mock_escalation,
        )

        result = await service.consult(**consultation_context)

        assert result.escalated is True
        assert result.escalation_level == EscalationLevel.ESCALATE
        assert result.response is not None  # Auto-message for escalation
        mock_response_chain.ainvoke.assert_not_called()

    async def test_monitor_level_still_returns_ai_response(
        self, mock_response_chain, consultation_context
    ):
        mock_escalation = AsyncMock()
        mock_escalation.detect.return_value = EscalationLevel.MONITOR

        service = ConsultationService(
            response_chain=mock_response_chain,
            escalation_detector=mock_escalation,
        )

        result = await service.consult(**consultation_context)

        assert result.escalated is False
        assert result.escalation_level == EscalationLevel.MONITOR
        assert result.response is not None
        mock_response_chain.ainvoke.assert_called_once()

    async def test_escalation_message_uses_persona_name(
        self, mock_response_chain, consultation_context
    ):
        mock_escalation = AsyncMock()
        mock_escalation.detect.return_value = EscalationLevel.ESCALATE

        service = ConsultationService(
            response_chain=mock_response_chain,
            escalation_detector=mock_escalation,
        )

        result = await service.consult(**consultation_context)

        # Auto-message should reference persona name
        assert "미소" in result.response

    async def test_consult_calls_escalation_with_query(
        self, service, mock_escalation_detector, consultation_context
    ):
        await service.consult(**consultation_context)

        mock_escalation_detector.detect.assert_called_once_with(
            consultation_context["query"], use_llm=True
        )
