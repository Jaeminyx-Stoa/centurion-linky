"""Knowledge Assembly Service — assembles RAG-like context from DB tables.

Uses hybrid search: vector similarity first, keyword fallback when embeddings
are unavailable or return insufficient results.
"""

import logging
import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.query_utils import escape_like
from app.models.clinic_procedure import ClinicProcedure
from app.models.medical_term import MedicalTerm
from app.models.procedure import Procedure
from app.models.response_library import ResponseLibrary

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Assembles knowledge context from response_library, procedures, and medical_terms."""

    def __init__(self, db: AsyncSession, vector_retriever=None):
        self.db = db
        self._retriever = vector_retriever

    async def assemble_knowledge(self, clinic_id: uuid.UUID, query: str) -> dict:
        """Build knowledge context for an AI consultation query.

        Returns {"rag_results": str, "clinic_manual": str}.
        """
        faqs = await self._search_response_library(clinic_id, query)
        procedures = await self._search_procedures(clinic_id, query)
        terms = await self._search_medical_terms(clinic_id, query)

        return {
            "rag_results": self._format_rag_results(faqs, procedures, terms),
            "clinic_manual": await self._load_clinic_manual(clinic_id),
        }

    async def _search_response_library(
        self, clinic_id: uuid.UUID, query: str
    ) -> list[ResponseLibrary]:
        """Hybrid search: vector first, keyword fallback."""
        vector_results = []
        if self._retriever:
            try:
                vector_results = await self._retriever.search_response_library(
                    clinic_id, query, limit=5
                )
            except Exception:
                logger.exception("Vector search failed for response_library")

        if len(vector_results) >= 3:
            return vector_results

        # Keyword fallback / supplement
        keyword_results = await self._keyword_search_response_library(clinic_id, query)

        # Merge: vector results first, then keyword results (deduplicated)
        seen_ids = {r.id for r in vector_results}
        merged = list(vector_results)
        for r in keyword_results:
            if r.id not in seen_ids:
                merged.append(r)
                seen_ids.add(r.id)
        return merged[:5]

    async def _keyword_search_response_library(
        self, clinic_id: uuid.UUID, query: str
    ) -> list[ResponseLibrary]:
        """Search FAQ entries by keyword matching."""
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        conditions = [
            or_(
                ResponseLibrary.question.ilike(f"%{escape_like(kw)}%", escape="\\"),
                ResponseLibrary.answer.ilike(f"%{escape_like(kw)}%", escape="\\"),
            )
            for kw in keywords
        ]

        result = await self.db.execute(
            select(ResponseLibrary)
            .where(
                ResponseLibrary.clinic_id == clinic_id,
                ResponseLibrary.is_active.is_(True),
                or_(*conditions),
            )
            .limit(5)
        )
        return list(result.scalars().all())

    async def _search_procedures(
        self, clinic_id: uuid.UUID, query: str
    ) -> list[dict]:
        """Hybrid search for procedures linked to the clinic."""
        vector_procs = []
        if self._retriever:
            try:
                vector_procs = await self._retriever.search_procedures(
                    clinic_id, query, limit=5
                )
            except Exception:
                logger.exception("Vector search failed for procedures")

        # If we have vector results, format them directly
        if vector_procs:
            results = []
            for proc in vector_procs:
                results.append({
                    "name": proc.name_ko,
                    "name_en": proc.name_en,
                    "description": proc.description_ko or "",
                    "effects": proc.effects_ko or "",
                    "duration_minutes": proc.duration_minutes,
                    "downtime_days": proc.downtime_days,
                    "precautions_after": proc.precautions_after or "",
                })
            if len(results) >= 3:
                return results

        # Keyword fallback
        keyword_results = await self._keyword_search_procedures(clinic_id, query)

        if not vector_procs:
            return keyword_results

        # Merge
        seen_names = {r["name"] for r in results}
        for r in keyword_results:
            if r["name"] not in seen_names:
                results.append(r)
                seen_names.add(r["name"])
        return results[:5]

    async def _keyword_search_procedures(
        self, clinic_id: uuid.UUID, query: str
    ) -> list[dict]:
        """Search procedures linked to the clinic by keyword matching."""
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        conditions = []
        for kw in keywords:
            escaped = escape_like(kw)
            conditions.append(
                or_(
                    Procedure.name_ko.ilike(f"%{escaped}%", escape="\\"),
                    Procedure.name_en.ilike(f"%{escaped}%", escape="\\"),
                    Procedure.name_ja.ilike(f"%{escaped}%", escape="\\"),
                    Procedure.description_ko.ilike(f"%{escaped}%", escape="\\"),
                )
            )

        result = await self.db.execute(
            select(ClinicProcedure)
            .join(Procedure)
            .where(
                ClinicProcedure.clinic_id == clinic_id,
                ClinicProcedure.is_active.is_(True),
                or_(*conditions),
            )
            .options(joinedload(ClinicProcedure.procedure))
            .limit(5)
        )
        clinic_procs = list(result.unique().scalars().all())

        results = []
        for cp in clinic_procs:
            proc = cp.procedure
            results.append({
                "name": proc.name_ko,
                "name_en": proc.name_en,
                "description": cp.custom_description or proc.description_ko or "",
                "effects": cp.custom_effects or proc.effects_ko or "",
                "duration_minutes": cp.custom_duration_minutes or proc.duration_minutes,
                "downtime_days": cp.custom_downtime_days or proc.downtime_days,
                "precautions_after": cp.custom_precautions_after or proc.precautions_after or "",
            })
        return results

    async def _search_medical_terms(
        self, clinic_id: uuid.UUID, query: str
    ) -> list[MedicalTerm]:
        """Hybrid search for medical terms."""
        vector_results = []
        if self._retriever:
            try:
                vector_results = await self._retriever.search_medical_terms(
                    clinic_id, query, limit=10
                )
            except Exception:
                logger.exception("Vector search failed for medical_terms")

        if len(vector_results) >= 5:
            return vector_results

        # Keyword fallback
        keyword_results = await self._keyword_search_medical_terms(clinic_id, query)

        # Merge
        seen_ids = {r.id for r in vector_results}
        merged = list(vector_results)
        for r in keyword_results:
            if r.id not in seen_ids:
                merged.append(r)
                seen_ids.add(r.id)
        return merged[:10]

    async def _keyword_search_medical_terms(
        self, clinic_id: uuid.UUID, query: str
    ) -> list[MedicalTerm]:
        """Search medical terms by keyword matching."""
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        conditions = [
            MedicalTerm.term_ko.ilike(f"%{escape_like(kw)}%", escape="\\")
            for kw in keywords
        ]

        result = await self.db.execute(
            select(MedicalTerm)
            .where(
                or_(
                    MedicalTerm.clinic_id == clinic_id,
                    MedicalTerm.clinic_id.is_(None),
                ),
                MedicalTerm.is_active.is_(True),
                or_(*conditions),
            )
            .limit(10)
        )
        return list(result.scalars().all())

    def _format_rag_results(
        self,
        faqs: list[ResponseLibrary],
        procedures: list[dict],
        terms: list[MedicalTerm],
    ) -> str:
        """Format matched knowledge into a single text block for the AI."""
        parts = []

        if faqs:
            faq_lines = []
            for faq in faqs:
                faq_lines.append(f"Q: {faq.question}\nA: {faq.answer}")
            parts.append("[FAQ]\n" + "\n\n".join(faq_lines))

        if procedures:
            proc_lines = []
            for p in procedures:
                line = f"- {p['name']}"
                if p.get("name_en"):
                    line += f" ({p['name_en']})"
                if p.get("description"):
                    line += f": {p['description']}"
                if p.get("duration_minutes"):
                    line += f" (시술시간: {p['duration_minutes']}분)"
                if p.get("downtime_days"):
                    line += f" (다운타임: {p['downtime_days']}일)"
                proc_lines.append(line)
            parts.append("[시술 정보]\n" + "\n".join(proc_lines))

        if terms:
            term_lines = [
                f"- {t.term_ko}: {t.description or ''}" for t in terms
            ]
            parts.append("[의료 용어]\n" + "\n".join(term_lines))

        return "\n\n".join(parts) if parts else ""

    async def _load_clinic_manual(self, clinic_id: uuid.UUID) -> str:
        """Load clinic manual from response_library general entries."""
        result = await self.db.execute(
            select(ResponseLibrary)
            .where(
                ResponseLibrary.clinic_id == clinic_id,
                ResponseLibrary.is_active.is_(True),
                ResponseLibrary.category == "general",
            )
            .limit(20)
        )
        entries = result.scalars().all()
        if not entries:
            return "클리닉 매뉴얼이 등록되지 않았습니다."

        lines = [f"Q: {e.question}\nA: {e.answer}" for e in entries]
        return "\n\n".join(lines)

    @staticmethod
    def _extract_keywords(query: str) -> list[str]:
        """Extract meaningful keywords from a query string."""
        # Remove common short particles/stopwords and split
        stopwords = {"이", "가", "을", "를", "은", "는", "에", "의", "와", "과",
                      "도", "로", "으로", "에서", "a", "the", "is", "are", "what",
                      "how", "i", "my", "me", "do", "can", "please"}
        words = query.strip().split()
        keywords = [w for w in words if len(w) >= 2 and w.lower() not in stopwords]
        return keywords[:5]  # Limit to 5 keywords
