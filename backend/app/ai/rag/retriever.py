"""Vector retriever — cosine similarity search against pgvector embeddings."""

import logging
import uuid

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import get_embeddings
from app.models.medical_term import MedicalTerm
from app.models.procedure import Procedure
from app.models.response_library import ResponseLibrary

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Performs vector similarity search over knowledge base tables."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embeddings = get_embeddings()

    async def search_response_library(
        self,
        clinic_id: uuid.UUID,
        query: str,
        limit: int = 5,
    ) -> list[ResponseLibrary]:
        """Search response_library by vector cosine similarity."""
        query_embedding = await self._embed_query(query)
        if query_embedding is None:
            return []

        result = await self.db.execute(
            select(ResponseLibrary)
            .where(
                ResponseLibrary.clinic_id == clinic_id,
                ResponseLibrary.embedding.is_not(None),
                ResponseLibrary.is_active.is_(True),
            )
            .order_by(ResponseLibrary.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_procedures(
        self,
        clinic_id: uuid.UUID,
        query: str,
        limit: int = 5,
    ) -> list[Procedure]:
        """Search procedures by vector cosine similarity."""
        query_embedding = await self._embed_query(query)
        if query_embedding is None:
            return []

        result = await self.db.execute(
            select(Procedure)
            .where(
                Procedure.embedding.is_not(None),
                Procedure.is_active.is_(True),
            )
            .order_by(Procedure.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_medical_terms(
        self,
        clinic_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[MedicalTerm]:
        """Search medical terms by vector cosine similarity."""
        query_embedding = await self._embed_query(query)
        if query_embedding is None:
            return []

        result = await self.db.execute(
            select(MedicalTerm)
            .where(
                or_(
                    MedicalTerm.clinic_id == clinic_id,
                    MedicalTerm.clinic_id.is_(None),
                ),
                MedicalTerm.embedding.is_not(None),
                MedicalTerm.is_active.is_(True),
            )
            .order_by(MedicalTerm.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _embed_query(self, query: str) -> list[float] | None:
        """Generate query embedding, returning None on failure."""
        try:
            return await self.embeddings.aembed_query(query)
        except Exception:
            logger.exception("Failed to generate query embedding")
            return None
