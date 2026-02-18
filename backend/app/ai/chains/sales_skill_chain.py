import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

SALES_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 미용의료 상담 전문가입니다.

[현재 대화 상황]
{conversation_history}

[세일즈 전략]
- 추천 우선순위 시술: {top_procedures}
- 현재 이벤트: {active_events}
- 크로스셀링 기회: {cross_sell_options}

[상담 패턴]
- 가격 질문 → 부위 먼저 질문 → 맞춤 가격 → 예약 유도
- 망설임 감지 → 이벤트/혜택 강조
- 경쟁 병원 언급 → 차별점 강조
- "생각해볼게요" → 부담 없는 상담 예약 제안

[규칙]
- 노골적 세일즈 금지 (자연스러운 흐름 유지)
- 고가 시술 문의 시 부담 적은 대안도 함께 제시
- 예약 유도는 자연스러운 질문 형태로
- 내부 세일즈 점수, 마진 정보 절대 노출 금지"""),
    ("human", "아래 답변에 자연스러운 세일즈 전략을 적용하세요:\n{styled_output}"),
])


class SalesSkillChain:
    """Layer 3: Applies natural sales strategy to the styled response."""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.prompt = SALES_PROMPT
        self._chain = self.prompt | self.llm | StrOutputParser()

    async def ainvoke(
        self,
        styled_output: str,
        conversation_history: str,
        sales_context: dict,
    ) -> str:
        top_procs = sales_context.get("top_procedures", [])
        events = sales_context.get("active_events", [])
        cross_sell = sales_context.get("cross_sell_options", [])

        return await self._chain.ainvoke({
            "styled_output": styled_output,
            "conversation_history": conversation_history or "(새 대화)",
            "top_procedures": json.dumps(top_procs, ensure_ascii=False) if top_procs else "(없음)",
            "active_events": json.dumps(events, ensure_ascii=False) if events else "(없음)",
            "cross_sell_options": json.dumps(cross_sell, ensure_ascii=False) if cross_sell else "(없음)",
        })
