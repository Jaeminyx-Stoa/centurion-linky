"""Escalation detection — keyword-based and LLM-based."""

import enum

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


class EscalationLevel(enum.Enum):
    NONE = "none"
    MONITOR = "monitor"
    ESCALATE = "escalate"


# Multilingual escalation keywords
ESCALATION_KEYWORDS = {
    "ko": ["부작용", "환불", "아파요", "피가", "신고", "불만", "고소"],
    "ja": ["副作用", "返金", "痛い", "血", "クレーム"],
    "en": ["side effect", "refund", "pain", "blood", "complaint", "lawsuit"],
    "zh": ["副作用", "退款", "疼", "血", "投诉"],
}

ESCALATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 미용의료 상담 메시지 분류기입니다.
다음 메시지가 어디에 해당하는지 숫자만 답하세요:
1. 일반 문의 (AI 처리 가능)
2. 주의 필요 (모니터링 권장)
3. 즉시 사람 연결 (컴플레인/부작용/의료사고/환불)"""),
    ("human", "메시지: {message}\n\n숫자만 답하세요 (1, 2, 또는 3):"),
])

_LEVEL_MAP = {
    "1": EscalationLevel.NONE,
    "2": EscalationLevel.MONITOR,
    "3": EscalationLevel.ESCALATE,
}


class EscalationDetector:
    """Detects if a customer message requires escalation to a human agent."""

    def __init__(self, light_llm: BaseChatModel):
        self.light_llm = light_llm
        self._chain = ESCALATION_PROMPT | self.light_llm | StrOutputParser()

    async def detect(
        self,
        message: str,
        use_llm: bool = False,
    ) -> EscalationLevel:
        # Fast path: keyword-based detection
        keyword_result = self._check_keywords(message)
        if keyword_result == EscalationLevel.ESCALATE:
            return EscalationLevel.ESCALATE

        # Slow path: LLM-based context detection
        if use_llm:
            return await self._classify_with_llm(message)

        return keyword_result

    def _check_keywords(self, message: str) -> EscalationLevel:
        message_lower = message.lower()
        for keywords in ESCALATION_KEYWORDS.values():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    return EscalationLevel.ESCALATE
        return EscalationLevel.NONE

    async def _classify_with_llm(self, message: str) -> EscalationLevel:
        result = await self._chain.ainvoke({"message": message})
        # Extract the first digit from the response
        for char in result.strip():
            if char in _LEVEL_MAP:
                return _LEVEL_MAP[char]
        return EscalationLevel.NONE
