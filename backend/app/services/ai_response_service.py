"""AIResponseService — orchestrates AI auto-response generation and delivery.

Coordinates: translation, knowledge assembly, cultural profiling, consultation,
humanlike behaviors, messenger delivery, and satisfaction tracking.
"""

import asyncio
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ab_test_engine import ABTestEngine
from app.ai.agents.consultation_service import ConsultationService
from app.ai.humanlike.delay import HumanLikeDelay
from app.ai.humanlike.disclosure import get_ai_disclosure
from app.ai.humanlike.greeting import get_time_greeting
from app.ai.satisfaction.analyzer import SatisfactionAnalyzer
from app.messenger.factory import MessengerAdapterFactory
from app.models.ab_test import ABTest
from app.models.ai_persona import AIPersona
from app.models.conversation import Conversation
from app.models.cultural_profile import CulturalProfile
from app.models.customer import Customer
from app.models.message import Message
from app.models.messenger_account import MessengerAccount
from app.services.knowledge_service import KnowledgeService
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


class AIResponseService:
    """Generates and delivers AI auto-responses for incoming customer messages."""

    def __init__(
        self,
        db: AsyncSession,
        consultation_service: ConsultationService,
        translation_chain=None,
    ):
        self.db = db
        self.consultation_service = consultation_service
        self.translation_chain = translation_chain

    async def generate_response(
        self,
        message_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Message | None:
        """Generate and send an AI response for a customer message.

        Returns the saved AI Message, or None if skipped.
        """
        # 1. Load context
        conversation = await self._load_conversation(conversation_id)
        if conversation is None:
            logger.warning("Conversation %s not found", conversation_id)
            return None

        # 2. Check ai_mode
        if not conversation.ai_mode:
            logger.info("AI mode OFF for conversation %s, skipping", conversation_id)
            return None

        # 3. Load related data
        customer = await self._load_customer(conversation.customer_id)
        messenger_account = await self._load_messenger_account(
            conversation.messenger_account_id
        )
        incoming_message = await self._load_message(message_id)

        if not customer or not messenger_account or not incoming_message:
            logger.warning("Missing data for AI response generation")
            return None

        language_code = customer.language_code or "ko"
        country_code = customer.country_code or "KR"

        # 4. Translate incoming message (if not Korean)
        query = incoming_message.content or ""
        if self.translation_chain and language_code != "ko":
            try:
                tr_result = await self.translation_chain.translate_incoming(
                    query, known_language=language_code
                )
                if not tr_result.skipped:
                    incoming_message.translated_content = tr_result.translated_text
                    incoming_message.translated_language = "ko"
                    query = tr_result.translated_text
            except Exception:
                logger.exception("Translation failed, using original text")

        # 5. Assemble knowledge
        knowledge_svc = KnowledgeService(self.db)
        knowledge = await knowledge_svc.assemble_knowledge(
            conversation.clinic_id, query
        )

        # 6. Load cultural profile + persona
        cultural_profile = await self._load_cultural_profile(country_code)
        persona = await self._load_persona(conversation.clinic_id)

        # 7. Load conversation history
        conversation_history = await self._load_conversation_history(conversation_id)

        # 7.5 A/B test variant selection
        ab_variant = await self._check_ab_tests(
            conversation.clinic_id, conversation_id, persona
        )

        # 8. Run consultation
        try:
            result = await self.consultation_service.consult(
                query=query,
                conversation_id=conversation_id,
                clinic_id=conversation.clinic_id,
                rag_results=knowledge["rag_results"],
                clinic_manual=knowledge["clinic_manual"],
                country_code=country_code,
                language_code=language_code,
                cultural_profile=cultural_profile,
                persona=persona,
                conversation_history=conversation_history,
                sales_context={},
            )
        except Exception:
            logger.exception("Consultation failed for conversation %s", conversation_id)
            return None

        # 9. Handle escalation
        if result.escalated:
            conversation.ai_mode = False
            conversation.status = "waiting"
            await manager.broadcast_to_clinic(
                conversation.clinic_id,
                {
                    "type": "escalation_alert",
                    "conversation_id": str(conversation_id),
                    "message": "AI 에스컬레이션: 상담사 연결 필요",
                },
            )

        # 10. Build final response text
        response_text = result.response
        is_first_message = await self._is_first_ai_message(conversation_id)

        if is_first_message:
            greeting = get_time_greeting(customer.timezone, language_code)
            disclosure = get_ai_disclosure(language_code)
            response_text = f"{greeting} {disclosure}\n\n{response_text}"

        # 11. Translate outgoing (if not Korean)
        if self.translation_chain and language_code != "ko":
            try:
                out_result = await self.translation_chain.translate_outgoing(
                    response_text, language_code
                )
                if not out_result.skipped:
                    response_text = out_result.translated_text
            except Exception:
                logger.exception("Outgoing translation failed")

        # 12. Typing delay
        delay = HumanLikeDelay.calculate_delay(response_text)
        await asyncio.sleep(delay)

        # 13. Save AI message
        ai_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            clinic_id=conversation.clinic_id,
            sender_type="ai",
            content=response_text,
            content_type="text",
            messenger_type=messenger_account.messenger_type,
        )
        self.db.add(ai_message)

        # Update conversation metadata
        conversation.last_message_preview = response_text[:200]
        await self.db.flush()

        # 14. Send via messenger
        try:
            adapter = MessengerAdapterFactory.get_adapter(
                messenger_account.messenger_type
            )
            await adapter.send_typing_indicator(
                messenger_account, customer.messenger_user_id
            )
            msg_id = await adapter.send_message(
                messenger_account,
                customer.messenger_user_id,
                response_text,
            )
            ai_message.messenger_message_id = msg_id
        except Exception:
            logger.exception("Failed to send message via messenger")

        # 15. WebSocket broadcast
        await manager.broadcast_to_clinic(
            conversation.clinic_id,
            {
                "type": "new_message",
                "conversation_id": str(conversation_id),
                "message": {
                    "id": str(ai_message.id),
                    "sender_type": "ai",
                    "content": response_text,
                    "content_type": "text",
                    "created_at": ai_message.created_at.isoformat()
                    if ai_message.created_at
                    else None,
                },
            },
        )

        # 16. Satisfaction analysis
        try:
            await self._update_satisfaction(conversation)
        except Exception:
            logger.exception("Satisfaction analysis failed")

        # 17. A/B test outcome recording
        if ab_variant:
            try:
                await self._record_ab_outcome(ab_variant, conversation)
            except Exception:
                logger.exception("A/B test outcome recording failed")

        return ai_message

    # --- Private helpers ---

    async def _load_conversation(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _load_customer(self, customer_id: uuid.UUID) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def _load_messenger_account(
        self, account_id: uuid.UUID
    ) -> MessengerAccount | None:
        result = await self.db.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def _load_message(self, message_id: uuid.UUID) -> Message | None:
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def _load_cultural_profile(self, country_code: str) -> dict:
        result = await self.db.execute(
            select(CulturalProfile).where(
                CulturalProfile.country_code == country_code,
                CulturalProfile.is_active.is_(True),
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            return {
                "country_name": country_code,
                "style_prompt": "",
                "preferred_expressions": {},
                "avoided_expressions": {},
                "emoji_level": "medium",
                "formality_level": "polite",
            }
        return {
            "country_name": profile.country_name,
            "style_prompt": profile.style_prompt or "",
            "preferred_expressions": profile.preferred_expressions or {},
            "avoided_expressions": profile.avoided_expressions or {},
            "emoji_level": profile.emoji_level,
            "formality_level": profile.formality_level,
        }

    async def _load_persona(self, clinic_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(AIPersona).where(
                AIPersona.clinic_id == clinic_id,
                AIPersona.is_active.is_(True),
                AIPersona.is_default.is_(True),
            )
        )
        persona = result.scalar_one_or_none()
        if persona is None:
            return {"name": "상담사", "personality": "친절하고 전문적인 AI 상담사"}
        return {
            "name": persona.name,
            "personality": persona.personality or "친절하고 전문적인 AI 상담사",
        }

    async def _load_conversation_history(self, conversation_id: uuid.UUID) -> str:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        messages = list(reversed(result.scalars().all()))
        if not messages:
            return ""

        lines = []
        for m in messages:
            role = {"customer": "고객", "ai": "AI", "staff": "상담사"}.get(
                m.sender_type, m.sender_type
            )
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines)

    async def _is_first_ai_message(self, conversation_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.sender_type == "ai",
            )
        )
        count = result.scalar() or 0
        return count == 0

    async def _check_ab_tests(
        self,
        clinic_id: uuid.UUID,
        conversation_id: uuid.UUID,
        persona: dict,
    ) -> dict | None:
        """Check for active A/B tests and select a variant."""
        try:
            result = await self.db.execute(
                select(ABTest).where(
                    ABTest.clinic_id == clinic_id,
                    ABTest.is_active.is_(True),
                )
            )
            active_test = result.scalars().first()
            if active_test is None:
                return None

            engine = ABTestEngine(self.db)
            variant = await engine.select_variant(active_test.id, conversation_id)
            if variant is None:
                return None

            # Apply variant config to persona if applicable
            config = variant.config or {}
            if "personality" in config:
                persona["personality"] = config["personality"]
            if "name" in config:
                persona["name"] = config["name"]

            return {
                "test_id": active_test.id,
                "variant_id": variant.id,
                "variant_name": variant.name,
            }
        except Exception:
            logger.exception("A/B test check failed")
            return None

    async def _record_ab_outcome(
        self, ab_variant: dict, conversation: Conversation
    ):
        """Record A/B test outcome based on conversation state."""
        engine = ABTestEngine(self.db)
        # Determine outcome based on satisfaction
        outcome = "responded"
        if conversation.satisfaction_score and conversation.satisfaction_score >= 70:
            outcome = "positive"

        await engine.record_outcome(
            test_id=ab_variant["test_id"],
            variant_id=ab_variant["variant_id"],
            conversation_id=conversation.id,
            outcome=outcome,
            outcome_data={"satisfaction_score": conversation.satisfaction_score},
        )

    async def _update_satisfaction(self, conversation: Conversation):
        """Update conversation satisfaction score from recent messages."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = list(reversed(result.scalars().all()))

        msg_dicts = [
            {
                "sender_type": m.sender_type,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ]

        analyzer = SatisfactionAnalyzer()
        analysis = analyzer.analyze(msg_dicts)
        conversation.satisfaction_score = analysis.score
        conversation.satisfaction_level = analysis.level
