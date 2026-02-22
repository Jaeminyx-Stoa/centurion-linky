"""Tests for KnowledgeIndexer — vector embedding generation."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.indexer import KnowledgeIndexer
from app.models.clinic import Clinic
from app.models.medical_term import MedicalTerm
from app.models.procedure import Procedure
from app.models.response_library import ResponseLibrary


@pytest.fixture
async def clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="인덱싱테스트", slug="test-indexer")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def faq_entries(db: AsyncSession, clinic: Clinic) -> list[ResponseLibrary]:
    entries = [
        ResponseLibrary(
            clinic_id=clinic.id,
            category="pricing",
            question="보톡스 가격이 얼마인가요?",
            answer="보톡스는 부위별 5만원~15만원입니다.",
        ),
        ResponseLibrary(
            clinic_id=clinic.id,
            category="procedure",
            question="필러 시술 시간은?",
            answer="필러는 약 30분 소요됩니다.",
        ),
    ]
    for e in entries:
        db.add(e)
    await db.commit()
    return entries


@pytest.fixture
async def procedures_data(db: AsyncSession) -> list[Procedure]:
    procs = [
        Procedure(
            id=uuid.uuid4(),
            name_ko="보톡스",
            name_en="Botox",
            slug="botox-idx",
            description_ko="주름 개선 시술",
        ),
    ]
    for p in procs:
        db.add(p)
    await db.commit()
    return procs


@pytest.fixture
async def medical_terms_data(db: AsyncSession, clinic: Clinic) -> list[MedicalTerm]:
    terms = [
        MedicalTerm(
            clinic_id=clinic.id,
            term_ko="보톡스",
            translations={"en": "Botox"},
            category="procedure",
            description="보툴리눔 독소를 이용한 주름 완화 시술",
        ),
    ]
    for t in terms:
        db.add(t)
    await db.commit()
    return terms


FAKE_EMBEDDING = [0.1] * 1536


@pytest.mark.asyncio
@patch("app.ai.rag.indexer.get_embeddings")
async def test_index_response_library(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, faq_entries
):
    """Should embed all un-indexed response_library entries."""
    mock_emb = MagicMock()
    mock_emb.aembed_documents = AsyncMock(
        return_value=[FAKE_EMBEDDING, FAKE_EMBEDDING]
    )
    mock_get_embeddings.return_value = mock_emb

    indexer = KnowledgeIndexer(db)
    count = await indexer.index_response_library(clinic.id)
    assert count == 2

    # Verify embeddings were stored
    for entry in faq_entries:
        await db.refresh(entry)
        assert entry.embedding is not None


@pytest.mark.asyncio
@patch("app.ai.rag.indexer.get_embeddings")
async def test_index_procedures(mock_get_embeddings, db: AsyncSession, procedures_data):
    """Should embed all un-indexed procedures."""
    mock_emb = MagicMock()
    mock_emb.aembed_documents = AsyncMock(return_value=[FAKE_EMBEDDING])
    mock_get_embeddings.return_value = mock_emb

    indexer = KnowledgeIndexer(db)
    count = await indexer.index_procedures()
    assert count == 1

    await db.refresh(procedures_data[0])
    assert procedures_data[0].embedding is not None


@pytest.mark.asyncio
@patch("app.ai.rag.indexer.get_embeddings")
async def test_index_medical_terms(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, medical_terms_data
):
    """Should embed all un-indexed medical terms."""
    mock_emb = MagicMock()
    mock_emb.aembed_documents = AsyncMock(return_value=[FAKE_EMBEDDING])
    mock_get_embeddings.return_value = mock_emb

    indexer = KnowledgeIndexer(db)
    count = await indexer.index_medical_terms()
    assert count == 1


@pytest.mark.asyncio
@patch("app.ai.rag.indexer.get_embeddings")
async def test_index_all(
    mock_get_embeddings,
    db: AsyncSession,
    clinic: Clinic,
    faq_entries,
    procedures_data,
    medical_terms_data,
):
    """index_all should return counts for all three tables."""
    mock_emb = MagicMock()
    mock_emb.aembed_documents = AsyncMock(
        side_effect=[
            [FAKE_EMBEDDING, FAKE_EMBEDDING],  # response_library
            [FAKE_EMBEDDING],  # procedures
            [FAKE_EMBEDDING],  # medical_terms
        ]
    )
    mock_get_embeddings.return_value = mock_emb

    indexer = KnowledgeIndexer(db)
    result = await indexer.index_all(clinic.id)
    assert result["response_library"] == 2
    assert result["procedures"] == 1
    assert result["medical_terms"] == 1


@pytest.mark.asyncio
@patch("app.ai.rag.indexer.get_embeddings")
async def test_already_indexed_skipped(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, faq_entries
):
    """Entries that already have embeddings should not be re-indexed."""
    # First pass: embed all
    mock_emb = MagicMock()
    mock_emb.aembed_documents = AsyncMock(
        return_value=[FAKE_EMBEDDING, FAKE_EMBEDDING]
    )
    mock_get_embeddings.return_value = mock_emb

    indexer = KnowledgeIndexer(db)
    await indexer.index_response_library(clinic.id)

    # Second pass: nothing should be indexed
    mock_emb.aembed_documents.reset_mock()
    count = await indexer.index_response_library(clinic.id)
    assert count == 0
    mock_emb.aembed_documents.assert_not_called()


@pytest.mark.asyncio
@patch("app.ai.rag.indexer.get_embeddings")
async def test_embedding_api_failure_graceful(
    mock_get_embeddings, db: AsyncSession, clinic: Clinic, faq_entries
):
    """API failure should be handled gracefully, returning 0."""
    mock_emb = MagicMock()
    mock_emb.aembed_documents = AsyncMock(side_effect=Exception("API error"))
    mock_get_embeddings.return_value = mock_emb

    indexer = KnowledgeIndexer(db)
    count = await indexer.index_response_library(clinic.id)
    assert count == 0
