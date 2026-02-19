"""Tests for KnowledgeService — keyword-based knowledge assembly."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.medical_term import MedicalTerm
from app.models.procedure import Procedure
from app.models.response_library import ResponseLibrary
from app.services.knowledge_service import KnowledgeService


@pytest.fixture
async def clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="테스트의원", slug="test-knowledge")
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
        ResponseLibrary(
            clinic_id=clinic.id,
            category="general",
            question="진료시간은?",
            answer="월~금 10:00~19:00, 토 10:00~15:00",
        ),
    ]
    for e in entries:
        db.add(e)
    await db.commit()
    return entries


@pytest.fixture
async def procedure_data(db: AsyncSession, clinic: Clinic) -> ClinicProcedure:
    proc = Procedure(
        id=uuid.uuid4(),
        name_ko="보톡스",
        name_en="Botox",
        slug="botox",
        description_ko="주름 개선 시술",
        duration_minutes=20,
        downtime_days=0,
    )
    db.add(proc)
    await db.flush()

    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        procedure_id=proc.id,
        is_active=True,
    )
    db.add(cp)
    await db.commit()
    return cp


@pytest.fixture
async def medical_terms(db: AsyncSession, clinic: Clinic) -> list[MedicalTerm]:
    terms = [
        MedicalTerm(
            clinic_id=clinic.id,
            term_ko="보톡스",
            translations={"en": "Botox", "ja": "ボトックス"},
            category="procedure",
            description="보툴리눔 독소를 이용한 주름 완화 시술",
        ),
        MedicalTerm(
            clinic_id=None,
            term_ko="필러",
            translations={"en": "Filler", "ja": "フィラー"},
            category="material",
            description="히알루론산 등을 주입하는 볼륨 시술",
        ),
    ]
    for t in terms:
        db.add(t)
    await db.commit()
    return terms


@pytest.mark.asyncio
async def test_assemble_knowledge_returns_required_keys(db: AsyncSession, clinic: Clinic):
    """assemble_knowledge must return dict with rag_results and clinic_manual keys."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스")
    assert "rag_results" in result
    assert "clinic_manual" in result


@pytest.mark.asyncio
async def test_faq_matching(db: AsyncSession, clinic: Clinic, faq_entries):
    """FAQ entries matching query keywords should appear in rag_results."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스 가격")
    assert "보톡스" in result["rag_results"]
    assert "5만원" in result["rag_results"]


@pytest.mark.asyncio
async def test_empty_result_for_no_match(db: AsyncSession, clinic: Clinic, faq_entries):
    """No matching keywords should produce empty rag_results."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "zzz_nomatch_xyz")
    assert result["rag_results"] == ""


@pytest.mark.asyncio
async def test_procedure_matching(db: AsyncSession, clinic: Clinic, procedure_data):
    """Procedures linked to the clinic should appear when matching."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스")
    assert "시술 정보" in result["rag_results"]
    assert "보톡스" in result["rag_results"]


@pytest.mark.asyncio
async def test_procedure_includes_duration(
    db: AsyncSession, clinic: Clinic, procedure_data
):
    """Procedure entries should include duration when available."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스")
    assert "20분" in result["rag_results"]


@pytest.mark.asyncio
async def test_internal_data_excluded(
    db: AsyncSession, clinic: Clinic, procedure_data
):
    """Internal business data (material_cost, difficulty_score) must not appear."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스")
    assert "material_cost" not in result["rag_results"]
    assert "difficulty_score" not in result["rag_results"]


@pytest.mark.asyncio
async def test_medical_term_matching(
    db: AsyncSession, clinic: Clinic, medical_terms
):
    """Medical terms matching query should appear in rag_results."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스")
    assert "의료 용어" in result["rag_results"]
    assert "보툴리눔" in result["rag_results"]


@pytest.mark.asyncio
async def test_format_sections(db: AsyncSession, clinic: Clinic, faq_entries, medical_terms):
    """Result should have proper section headers."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "보톡스")
    text = result["rag_results"]
    assert "[FAQ]" in text or "[의료 용어]" in text


@pytest.mark.asyncio
async def test_clinic_manual_loads_general_entries(
    db: AsyncSession, clinic: Clinic, faq_entries
):
    """clinic_manual should contain general category FAQ entries."""
    svc = KnowledgeService(db)
    result = await svc.assemble_knowledge(clinic.id, "anything")
    assert "진료시간" in result["clinic_manual"]


@pytest.mark.asyncio
async def test_empty_clinic_default_manual(db: AsyncSession):
    """Clinic with no entries should get a default manual message."""
    empty_clinic_id = uuid.uuid4()
    svc = KnowledgeService(db)
    manual = await svc._load_clinic_manual(empty_clinic_id)
    assert "등록되지 않았습니다" in manual
