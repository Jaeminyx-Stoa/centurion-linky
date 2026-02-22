"""Celery tasks for knowledge base vector indexing."""

import asyncio
import logging

from celery import Task

from app.tasks import celery_app

logger = logging.getLogger(__name__)


class IndexingTask(Task):
    """Base task class for indexing operations."""

    _loop = None

    @property
    def loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop


@celery_app.task(
    base=IndexingTask,
    bind=True,
    name="app.tasks.indexing.reindex_clinic",
    max_retries=2,
    soft_time_limit=300,
    time_limit=360,
)
def reindex_clinic(self: IndexingTask, clinic_id: str) -> dict:
    """Reindex all knowledge for a specific clinic."""
    import uuid

    logger.info("Reindexing knowledge for clinic=%s", clinic_id)
    try:
        result = self.loop.run_until_complete(
            _reindex_clinic(uuid.UUID(clinic_id))
        )
        logger.info("Reindex complete for clinic=%s: %s", clinic_id, result)
        return result
    except Exception as exc:
        logger.exception("Reindex failed for clinic=%s", clinic_id)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(
    base=IndexingTask,
    bind=True,
    name="app.tasks.indexing.reindex_pending",
    max_retries=1,
    soft_time_limit=600,
    time_limit=720,
)
def reindex_pending(self: IndexingTask) -> dict:
    """Periodic task: index all records with embedding IS NULL across all clinics."""
    logger.info("Batch reindex sweep started")
    try:
        result = self.loop.run_until_complete(_reindex_pending())
        logger.info("Batch reindex sweep finished: %s", result)
        return result
    except Exception as exc:
        logger.exception("Batch reindex sweep failed")
        raise self.retry(exc=exc, countdown=120)


async def _reindex_clinic(clinic_id) -> dict:
    from app.ai.rag.indexer import KnowledgeIndexer
    from app.core.database import async_session_factory

    async with async_session_factory() as db:
        try:
            indexer = KnowledgeIndexer(db)
            result = await indexer.index_all(clinic_id)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise


async def _reindex_pending() -> dict:
    from sqlalchemy import select

    from app.ai.rag.indexer import KnowledgeIndexer
    from app.core.database import async_session_factory
    from app.models.clinic import Clinic

    totals = {"response_library": 0, "procedures": 0, "medical_terms": 0}

    async with async_session_factory() as db:
        try:
            # Get all active clinics
            result = await db.execute(
                select(Clinic).where(Clinic.is_active.is_(True))
            )
            clinics = result.scalars().all()

            indexer = KnowledgeIndexer(db)

            # Index procedures and medical terms (global, not per-clinic)
            totals["procedures"] = await indexer.index_procedures()
            totals["medical_terms"] = await indexer.index_medical_terms()

            # Index per-clinic response_library
            for clinic in clinics:
                count = await indexer.index_response_library(clinic.id)
                totals["response_library"] += count

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return totals
