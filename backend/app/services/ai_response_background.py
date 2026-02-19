"""Background task wrappers for AI response generation and WebSocket broadcast."""

import logging
import uuid
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.agents.consultation_service import ConsultationService
from app.ai.agents.escalation import EscalationDetector
from app.ai.chains.response_chain import ResponseChain
from app.services.ai_response_service import AIResponseService
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def broadcast_incoming_message(
    message, clinic_id: uuid.UUID
) -> None:
    """Broadcast an incoming customer message to the clinic dashboard via WebSocket."""
    await manager.broadcast_to_clinic(
        clinic_id,
        {
            "type": "new_message",
            "conversation_id": str(message.conversation_id),
            "message": {
                "id": str(message.id),
                "sender_type": message.sender_type,
                "content": message.content,
                "content_type": message.content_type,
                "created_at": message.created_at.isoformat()
                if message.created_at
                else None,
            },
        },
    )


def _build_consultation_service() -> ConsultationService:
    """Build ConsultationService with LLM chains.

    Lazy import to avoid circular imports and defer LLM initialization.
    """
    from app.ai.chains.knowledge_chain import KnowledgeChain
    from app.ai.chains.sales_skill_chain import SalesSkillChain
    from app.ai.chains.style_chain import StyleChain
    from app.ai.llm_router import get_consultation_llm, get_light_llm

    llm = get_consultation_llm()
    light_llm = get_light_llm()

    knowledge_chain = KnowledgeChain(llm)
    style_chain = StyleChain(llm)
    sales_chain = SalesSkillChain(llm)
    response_chain = ResponseChain(knowledge_chain, style_chain, sales_chain)
    escalation_detector = EscalationDetector(light_llm)

    return ConsultationService(response_chain, escalation_detector)


def _build_translation_chain():
    """Build TranslationChain with LLM. Returns None if setup fails."""
    try:
        from app.ai.chains.translation_chain import TranslationChain
        from app.ai.llm_router import get_consultation_llm, get_light_llm

        return TranslationChain(
            translation_llm=get_consultation_llm(),
            detection_llm=get_light_llm(),
            term_dict={},
        )
    except Exception:
        logger.warning("TranslationChain setup failed, translations disabled")
        return None


async def process_ai_response_background(
    message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    consultation_service: ConsultationService | None = None,
    translation_chain=None,
) -> None:
    """Background task: generate and deliver AI response.

    Creates its own DB session so it runs independently of the request lifecycle.
    """
    if consultation_service is None:
        consultation_service = _build_consultation_service()

    async with session_factory() as db:
        try:
            service = AIResponseService(
                db=db,
                consultation_service=consultation_service,
                translation_chain=translation_chain,
            )
            await service.generate_response(
                message_id=message_id,
                conversation_id=conversation_id,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception(
                "AI response background task failed for message %s", message_id
            )
