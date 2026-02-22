"""Knowledge indexer — generates and stores vector embeddings for RAG."""

import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import get_embeddings
from app.models.medical_term import MedicalTerm
from app.models.procedure import Procedure
from app.models.response_library import ResponseLibrary

logger = logging.getLogger(__name__)

BATCH_SIZE = 20


class KnowledgeIndexer:
    """Generates vector embeddings for knowledge base records."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embeddings = get_embeddings()

    async def index_response_library(self, clinic_id: uuid.UUID) -> int:
        """Embed all un-indexed response_library entries for a clinic."""
        result = await self.db.execute(
            select(ResponseLibrary)
            .where(
                ResponseLibrary.clinic_id == clinic_id,
                ResponseLibrary.embedding.is_(None),
                ResponseLibrary.is_active.is_(True),
            )
            .limit(200)
        )
        entries = list(result.scalars().all())
        if not entries:
            return 0

        texts = [f"{e.question}\n{e.answer}" for e in entries]
        count = await self._embed_and_store(entries, texts)
        logger.info("Indexed %d response_library entries for clinic %s", count, clinic_id)
        return count

    async def index_procedures(self, clinic_id: uuid.UUID | None = None) -> int:
        """Embed all un-indexed procedures."""
        stmt = select(Procedure).where(
            Procedure.embedding.is_(None),
            Procedure.is_active.is_(True),
        )
        if clinic_id is not None:
            # Index all procedures (global table, not clinic-scoped)
            pass
        result = await self.db.execute(stmt.limit(200))
        entries = list(result.scalars().all())
        if not entries:
            return 0

        texts = []
        for p in entries:
            parts = [p.name_ko]
            if p.name_en:
                parts.append(p.name_en)
            if p.description_ko:
                parts.append(p.description_ko)
            if p.effects_ko:
                parts.append(p.effects_ko)
            texts.append(" ".join(parts))

        count = await self._embed_and_store(entries, texts)
        logger.info("Indexed %d procedures", count)
        return count

    async def index_medical_terms(self, clinic_id: uuid.UUID | None = None) -> int:
        """Embed all un-indexed medical terms."""
        stmt = select(MedicalTerm).where(
            MedicalTerm.embedding.is_(None),
            MedicalTerm.is_active.is_(True),
        )
        result = await self.db.execute(stmt.limit(200))
        entries = list(result.scalars().all())
        if not entries:
            return 0

        texts = []
        for t in entries:
            parts = [t.term_ko]
            if t.description:
                parts.append(t.description)
            texts.append(" ".join(parts))

        count = await self._embed_and_store(entries, texts)
        logger.info("Indexed %d medical terms", count)
        return count

    async def index_all(self, clinic_id: uuid.UUID) -> dict:
        """Index all knowledge for a clinic."""
        rl = await self.index_response_library(clinic_id)
        proc = await self.index_procedures(clinic_id)
        terms = await self.index_medical_terms(clinic_id)
        return {"response_library": rl, "procedures": proc, "medical_terms": terms}

    async def _embed_and_store(self, entries: list, texts: list[str]) -> int:
        """Batch embed texts and update corresponding model records."""
        count = 0
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i : i + BATCH_SIZE]
            batch_entries = entries[i : i + BATCH_SIZE]

            try:
                vectors = await self.embeddings.aembed_documents(batch_texts)
            except Exception:
                logger.exception("Embedding API call failed for batch starting at %d", i)
                continue

            for entry, vector in zip(batch_entries, vectors):
                entry.embedding = vector
                count += 1

        await self.db.flush()
        return count
