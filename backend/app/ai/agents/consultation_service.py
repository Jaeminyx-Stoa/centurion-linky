"""ConsultationService — main orchestrator for AI consultations."""

import logging
import uuid
from dataclasses import dataclass

from app.ai.agents.escalation import EscalationDetector, EscalationLevel
from app.ai.chains.response_chain import ResponseChain

logger = logging.getLogger(__name__)

ESCALATION_MESSAGE_TEMPLATE = (
    "{persona_name}: 더 정확한 안내를 위해 "
    "전문 상담사가 곧 연결됩니다. 잠시만 기다려주세요\U0001f60a"
)


@dataclass
class ConsultationResult:
    response: str
    escalated: bool
    escalation_level: EscalationLevel
    conversation_id: uuid.UUID | None = None


class ConsultationService:
    """Orchestrates AI consultation with escalation checks."""

    def __init__(
        self,
        response_chain: ResponseChain,
        escalation_detector: EscalationDetector,
        agent=None,
    ):
        self.response_chain = response_chain
        self.escalation_detector = escalation_detector
        self.agent = agent

    async def consult(
        self,
        query: str,
        conversation_id: uuid.UUID,
        clinic_id: uuid.UUID,
        rag_results: str,
        clinic_manual: str,
        country_code: str,
        language_code: str,
        cultural_profile: dict,
        persona: dict,
        conversation_history: str,
        sales_context: dict,
    ) -> ConsultationResult:
        # Step 1: Check escalation
        escalation_level = await self.escalation_detector.detect(
            query, use_llm=True
        )

        # Step 2: If ESCALATE, return auto-message without AI response
        if escalation_level == EscalationLevel.ESCALATE:
            auto_message = ESCALATION_MESSAGE_TEMPLATE.format(
                persona_name=persona.get("name", "상담사"),
            )
            return ConsultationResult(
                response=auto_message,
                escalated=True,
                escalation_level=escalation_level,
                conversation_id=conversation_id,
            )

        # Step 3: Try agent if available
        if self.agent:
            try:
                response = await self.agent.ainvoke(
                    input=query,
                    chat_history=[],
                    persona_name=persona.get("name", "상담사"),
                    persona_personality=persona.get("personality", ""),
                    rag_results=rag_results,
                    clinic_manual=clinic_manual,
                    language_code=language_code,
                    cultural_context=cultural_profile.get("style_prompt", ""),
                )
                return ConsultationResult(
                    response=response,
                    escalated=False,
                    escalation_level=escalation_level,
                    conversation_id=conversation_id,
                )
            except Exception:
                logger.exception(
                    "Agent failed for conversation %s, falling back to chain",
                    conversation_id,
                )

        # Step 4: Fallback to 3-layer response chain
        response = await self.response_chain.ainvoke(
            query=query,
            rag_results=rag_results,
            clinic_manual=clinic_manual,
            country_code=country_code,
            language_code=language_code,
            cultural_profile=cultural_profile,
            persona=persona,
            conversation_history=conversation_history,
            sales_context=sales_context,
        )

        return ConsultationResult(
            response=response,
            escalated=False,
            escalation_level=escalation_level,
            conversation_id=conversation_id,
        )
