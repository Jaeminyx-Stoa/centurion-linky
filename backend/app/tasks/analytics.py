"""Celery tasks for periodic analytics: performance, settlements, conversation summaries."""

import asyncio
import logging
from datetime import datetime, timezone

from celery import Task

from app.tasks import celery_app

logger = logging.getLogger(__name__)


class AnalyticsTask(Task):
    """Base task class for analytics operations."""

    _loop = None

    @property
    def loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop


@celery_app.task(
    base=AnalyticsTask,
    bind=True,
    name="app.tasks.analytics.calculate_monthly_performance",
    max_retries=2,
    soft_time_limit=300,
    time_limit=360,
)
def calculate_monthly_performance(self: AnalyticsTask) -> dict:
    """Monthly task (1st of month): calculate previous month's consultation performance."""
    logger.info("Monthly performance calculation started")
    try:
        result = self.loop.run_until_complete(_calculate_monthly_performance())
        logger.info("Monthly performance done: %s", result)
        return result
    except Exception as exc:
        logger.exception("Monthly performance calculation failed")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(
    base=AnalyticsTask,
    bind=True,
    name="app.tasks.analytics.generate_monthly_settlements",
    max_retries=2,
    soft_time_limit=300,
    time_limit=360,
)
def generate_monthly_settlements(self: AnalyticsTask) -> dict:
    """Monthly task (1st of month): generate previous month's settlements for all clinics."""
    logger.info("Monthly settlements generation started")
    try:
        result = self.loop.run_until_complete(_generate_monthly_settlements())
        logger.info("Monthly settlements done: %s", result)
        return result
    except Exception as exc:
        logger.exception("Monthly settlements generation failed")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(
    base=AnalyticsTask,
    bind=True,
    name="app.tasks.analytics.summarize_conversations",
    max_retries=1,
    soft_time_limit=600,
    time_limit=720,
)
def summarize_conversations(self: AnalyticsTask) -> dict:
    """Hourly task: summarize long conversations without summaries."""
    logger.info("Conversation summarization sweep started")
    try:
        result = self.loop.run_until_complete(_summarize_conversations())
        logger.info("Conversation summarization done: %s", result)
        return result
    except Exception as exc:
        logger.exception("Conversation summarization failed")
        raise self.retry(exc=exc, countdown=60)


async def _calculate_monthly_performance() -> dict:
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.clinic import Clinic
    from app.services.performance_service import PerformanceService

    now = datetime.now(timezone.utc)
    # Previous month
    if now.month == 1:
        year, month = now.year - 1, 12
    else:
        year, month = now.year, now.month - 1

    count = 0
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Clinic).where(Clinic.is_active.is_(True))
            )
            clinics = result.scalars().all()

            service = PerformanceService(db)
            for clinic in clinics:
                await service.calculate_performance(clinic.id, year, month)
                count += 1

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return {"year": year, "month": month, "clinics_processed": count}


async def _generate_monthly_settlements() -> dict:
    from app.core.database import async_session_factory
    from app.services.settlement_service import SettlementService

    now = datetime.now(timezone.utc)
    if now.month == 1:
        year, month = now.year - 1, 12
    else:
        year, month = now.year, now.month - 1

    async with async_session_factory() as db:
        try:
            service = SettlementService(db)
            settlements = await service.generate_all_settlements(year, month)
            await db.commit()
            return {
                "year": year,
                "month": month,
                "settlements_generated": len(settlements),
            }
        except Exception:
            await db.rollback()
            raise


async def _summarize_conversations() -> dict:
    from sqlalchemy import func, select

    from app.ai.memory.summarizer import ConversationSummarizer
    from app.core.database import async_session_factory
    from app.models.conversation import Conversation
    from app.models.message import Message

    summarized = 0

    async with async_session_factory() as db:
        try:
            # Find conversations with >20 messages and no summary
            subq = (
                select(
                    Message.conversation_id,
                    func.count(Message.id).label("msg_count"),
                )
                .group_by(Message.conversation_id)
                .having(func.count(Message.id) > 20)
                .subquery()
            )

            result = await db.execute(
                select(Conversation)
                .join(subq, Conversation.id == subq.c.conversation_id)
                .where(Conversation.summary.is_(None))
                .limit(20)
            )
            conversations = result.scalars().all()

            if not conversations:
                await db.commit()
                return {"summarized": 0}

            summarizer = ConversationSummarizer()

            for conv in conversations:
                try:
                    msg_result = await db.execute(
                        select(Message)
                        .where(Message.conversation_id == conv.id)
                        .order_by(Message.created_at.asc())
                        .limit(50)
                    )
                    messages = msg_result.scalars().all()
                    msg_dicts = [
                        {"sender_type": m.sender_type, "content": m.content or ""}
                        for m in messages
                    ]
                    conv.summary = await summarizer.summarize(msg_dicts)
                    summarized += 1
                except Exception:
                    logger.exception("Failed to summarize conversation %s", conv.id)

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return {"summarized": summarized}
