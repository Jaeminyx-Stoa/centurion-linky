"""Celery tasks for AI response generation."""

import asyncio
import logging
import uuid

from celery import Task

from app.tasks import celery_app

logger = logging.getLogger(__name__)


class AIResponseTask(Task):
    """Base task class with lazy-loaded AI services."""

    _consultation_service = None
    _translation_chain = None

    @property
    def consultation_service(self):
        if self._consultation_service is None:
            from app.services.ai_response_background import (
                _build_consultation_service,
            )

            self._consultation_service = _build_consultation_service()
        return self._consultation_service

    @property
    def translation_chain(self):
        if self._translation_chain is None:
            from app.services.ai_response_background import (
                _build_translation_chain,
            )

            self._translation_chain = _build_translation_chain()
        return self._translation_chain


@celery_app.task(
    base=AIResponseTask,
    bind=True,
    name="app.tasks.ai_response.generate",
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=120,
    time_limit=180,
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_ai_response(
    self: AIResponseTask,
    message_id: str,
    conversation_id: str,
    idempotency_key: str | None = None,
) -> dict:
    """Generate AI response for an incoming message.

    Args:
        message_id: UUID of the incoming customer message.
        conversation_id: UUID of the conversation.
        idempotency_key: Optional key to prevent duplicate processing.

    Returns:
        dict with status and details.
    """
    task_id = self.request.id
    logger.info(
        "AI response task started: message=%s conversation=%s task=%s retry=%d",
        message_id,
        conversation_id,
        task_id,
        self.request.retries,
    )

    try:
        result = asyncio.get_event_loop().run_until_complete(
            _run_ai_response(
                self,
                uuid.UUID(message_id),
                uuid.UUID(conversation_id),
                idempotency_key,
            )
        )
        return result
    except Exception as exc:
        logger.exception(
            "AI response task failed: message=%s task=%s retry=%d",
            message_id,
            task_id,
            self.request.retries,
        )
        raise self.retry(exc=exc)


async def _run_ai_response(
    task: AIResponseTask,
    message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    idempotency_key: str | None,
) -> dict:
    """Async implementation of AI response generation."""
    from app.core.database import async_session_factory
    from app.models.message import Message
    from app.services.ai_response_service import AIResponseService

    async with async_session_factory() as db:
        try:
            # Idempotency check: skip if AI already replied to this message
            if idempotency_key:
                from sqlalchemy import select

                existing = await db.execute(
                    select(Message).where(
                        Message.conversation_id == conversation_id,
                        Message.sender_type == "ai",
                        Message.ai_metadata["idempotency_key"].as_string()
                        == idempotency_key,
                    )
                )
                if existing.scalar_one_or_none():
                    logger.info(
                        "Skipping duplicate: idempotency_key=%s", idempotency_key
                    )
                    return {"status": "skipped", "reason": "duplicate"}

            service = AIResponseService(
                db=db,
                consultation_service=task.consultation_service,
                translation_chain=task.translation_chain,
            )
            await service.generate_response(
                message_id=message_id,
                conversation_id=conversation_id,
            )
            await db.commit()
            return {"status": "success", "message_id": str(message_id)}
        except Exception:
            await db.rollback()
            raise
