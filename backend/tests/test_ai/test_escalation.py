import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.ai.agents.escalation import EscalationDetector, EscalationLevel


class TestKeywordEscalation:
    """Keyword-based escalation detection (fast path)."""

    @pytest.fixture
    def detector(self):
        fake_llm = GenericFakeChatModel(messages=iter([AIMessage(content="1")]))
        return EscalationDetector(light_llm=fake_llm)

    @pytest.mark.parametrize("message,expected", [
        # Korean escalation keywords
        ("부작용이 심해요", EscalationLevel.ESCALATE),
        ("환불해주세요", EscalationLevel.ESCALATE),
        ("너무 아파요 도와주세요", EscalationLevel.ESCALATE),
        ("피가 나요", EscalationLevel.ESCALATE),
        ("고소할거예요", EscalationLevel.ESCALATE),
        ("불만이 있습니다", EscalationLevel.ESCALATE),
        # Japanese
        ("副作用がひどいです", EscalationLevel.ESCALATE),
        ("返金してください", EscalationLevel.ESCALATE),
        ("痛いです", EscalationLevel.ESCALATE),
        ("クレームです", EscalationLevel.ESCALATE),
        # English
        ("I'm experiencing side effects", EscalationLevel.ESCALATE),
        ("I want a refund", EscalationLevel.ESCALATE),
        ("I'm in pain", EscalationLevel.ESCALATE),
        ("I want to file a complaint", EscalationLevel.ESCALATE),
        # Chinese
        ("有副作用", EscalationLevel.ESCALATE),
        ("我要退款", EscalationLevel.ESCALATE),
        ("投诉", EscalationLevel.ESCALATE),
        # Normal messages (no keyword match)
        ("보톡스 가격이 어떻게 되나요?", EscalationLevel.NONE),
        ("予約したいです", EscalationLevel.NONE),
        ("What procedures do you offer?", EscalationLevel.NONE),
        ("你们有什么项目？", EscalationLevel.NONE),
    ])
    async def test_keyword_detection(self, detector, message, expected):
        result = await detector.detect(message)
        assert result == expected


class TestLLMEscalation:
    """LLM-based context escalation detection."""

    async def test_llm_detects_escalation(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="3")])
        )
        detector = EscalationDetector(light_llm=fake_llm)
        # A message without keyword but LLM classifies as escalation
        result = await detector.detect(
            "시술 후 얼굴이 이상해졌어요 어떡하죠",
            use_llm=True,
        )
        assert result == EscalationLevel.ESCALATE

    async def test_llm_detects_monitor(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="2")])
        )
        detector = EscalationDetector(light_llm=fake_llm)
        result = await detector.detect(
            "시술이 좀 걱정되네요",
            use_llm=True,
        )
        assert result == EscalationLevel.MONITOR

    async def test_llm_detects_normal(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="1")])
        )
        detector = EscalationDetector(light_llm=fake_llm)
        result = await detector.detect(
            "보톡스 시술 시간이 얼마나 걸리나요?",
            use_llm=True,
        )
        assert result == EscalationLevel.NONE

    async def test_keyword_takes_priority_over_llm(self):
        """If keyword matches ESCALATE, don't need LLM."""
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="1")])  # LLM says normal
        )
        detector = EscalationDetector(light_llm=fake_llm)
        result = await detector.detect("환불 요청합니다")
        assert result == EscalationLevel.ESCALATE
