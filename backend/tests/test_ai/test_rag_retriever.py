"""Tests for VectorRetriever — vector similarity search."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.retriever import VectorRetriever
from app.models.clinic import Clinic
from app.models.medical_term import MedicalTerm
from app.models.procedure import Procedure
from app.models.response_library import ResponseLibrary

FAKE_EMBEDDING = [0.1] * 1536
FAKE_QUERY_EMBEDDING = [0.2] * 1536


@pytest.fixture
async def clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="검색테스트", slug="test-retriever")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def indexed_faqs(db: AsyncSession, clinic: Clinic) -> list[ResponseLibrary]:
    entries = [
        ResponseLibrary(
            clinic_id=clinic.id,
            category="pricing",
            question="보톡스 가격이 얼마인가요?",
            answer="보톡스는 부위별 5만원~15만원입니다.",
            embedding=FAKE_EMBEDDING,
        ),
        ResponseLibrary(
            clinic_id=clinic.id,
            category="procedure",
            question="필러 시술 시간은?",
            answer="필러는 약 30분 소요됩니다.",
            embedding=FAKE_EMBEDDING,
        ),
        ResponseLibrary(
            clinic_id=clinic.id,
            category="general",
            question="진료시간은?",
            answer="월~금 10:00~19:00",
            # No embedding — should not appear in vector results
        ),
    ]
    for e in entries:
        db.add(e)
    await db.commit()
    return entries


@pytest.fixture
async def indexed_procedures(db: AsyncSession) -> list[Procedure]:
    procs = [
        Procedure(
            id=uuid.uuid4(),
            name_ko="보톡스",
            name_en="Botox",
            slug="botox-ret",
            embedding=FAKE_EMBEDDING,
        ),
    ]
    for p in procs:
        db.add(p)
    await db.commit()
    return procs


@pytest.fixture
async def indexed_terms(db: AsyncSession, clinic: Clinic) -> list[MedicalTerm]:
    terms = [
        MedicalTerm(
            clinic_id=clinic.id,
            term_ko="보톡스",
            translations={"en": "Botox"},
            category="procedure",
            description="보툴리눔 독소 주름 완화",
            embedding=FAKE_EMBEDDING,
        ),
    ]
    for t in terms:
        db.add(t)
    await db.commit()
    return terms


@pytest.mark.asyncio
@patch("app.ai.rag.retriever.get_embeddings")
async def test_search_response_library(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, indexed_faqs
):
    """Should return only entries with embeddings, ordered by similarity."""
    mock_emb = MagicMock()
    mock_emb.aembed_query = AsyncMock(return_value=FAKE_QUERY_EMBEDDING)
    mock_get_embeddings.return_value = mock_emb

    retriever = VectorRetriever(db)
    results = await retriever.search_response_library(clinic.id, "보톡스 가격")
    assert len(results) == 2  # Only entries with embeddings
    assert all(r.embedding is not None for r in results)


@pytest.mark.asyncio
@patch("app.ai.rag.retriever.get_embeddings")
async def test_search_procedures(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, indexed_procedures
):
    """Should return procedures with embeddings."""
    mock_emb = MagicMock()
    mock_emb.aembed_query = AsyncMock(return_value=FAKE_QUERY_EMBEDDING)
    mock_get_embeddings.return_value = mock_emb

    retriever = VectorRetriever(db)
    results = await retriever.search_procedures(clinic.id, "보톡스")
    assert len(results) == 1
    assert results[0].name_ko == "보톡스"


@pytest.mark.asyncio
@patch("app.ai.rag.retriever.get_embeddings")
async def test_search_medical_terms(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, indexed_terms
):
    """Should return medical terms with embeddings."""
    mock_emb = MagicMock()
    mock_emb.aembed_query = AsyncMock(return_value=FAKE_QUERY_EMBEDDING)
    mock_get_embeddings.return_value = mock_emb

    retriever = VectorRetriever(db)
    results = await retriever.search_medical_terms(clinic.id, "보톡스")
    assert len(results) == 1
    assert results[0].term_ko == "보톡스"


@pytest.mark.asyncio
@patch("app.ai.rag.retriever.get_embeddings")
async def test_embed_query_failure_returns_empty(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic
):
    """If embedding query fails, should return empty list."""
    mock_emb = MagicMock()
    mock_emb.aembed_query = AsyncMock(side_effect=Exception("API error"))
    mock_get_embeddings.return_value = mock_emb

    retriever = VectorRetriever(db)
    results = await retriever.search_response_library(clinic.id, "test")
    assert results == []


@pytest.mark.asyncio
@patch("app.ai.rag.retriever.get_embeddings")
async def test_empty_table_returns_empty(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic
):
    """Empty table should return empty list."""
    mock_emb = MagicMock()
    mock_emb.aembed_query = AsyncMock(return_value=FAKE_QUERY_EMBEDDING)
    mock_get_embeddings.return_value = mock_emb

    retriever = VectorRetriever(db)
    results = await retriever.search_response_library(clinic.id, "anything")
    assert results == []
