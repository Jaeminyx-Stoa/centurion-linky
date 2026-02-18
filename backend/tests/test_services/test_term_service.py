import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clinic, MedicalTerm
from app.services.term_service import load_term_dict


@pytest.fixture
async def seed_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="시드의원", slug="seed-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


class TestLoadTermDict:
    async def test_loads_global_terms(self, db: AsyncSession):
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=None,
            term_ko="보톡스",
            translations={"ja": "ボトックス", "en": "Botox"},
            category="procedure",
        ))
        await db.commit()

        result = await load_term_dict(db)
        assert result["ja"]["ボトックス"] == "보톡스"
        assert result["en"]["Botox"] == "보톡스"

    async def test_includes_clinic_terms(
        self, db: AsyncSession, seed_clinic: Clinic
    ):
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=seed_clinic.id,
            term_ko="물광주사",
            translations={"ja": "水光注射"},
            category="procedure",
        ))
        await db.commit()

        result = await load_term_dict(db, clinic_id=seed_clinic.id)
        assert result["ja"]["水光注射"] == "물광주사"

    async def test_clinic_overrides_global(
        self, db: AsyncSession, seed_clinic: Clinic
    ):
        # Global term
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=None,
            term_ko="보톡스",
            translations={"ja": "ボトックス"},
            category="procedure",
        ))
        # Clinic override with different korean name
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=seed_clinic.id,
            term_ko="보톡스주사",
            translations={"ja": "ボトックス"},
            category="procedure",
        ))
        await db.commit()

        result = await load_term_dict(db, clinic_id=seed_clinic.id)
        # Clinic term should override global (loaded after due to ordering)
        assert result["ja"]["ボトックス"] == "보톡스주사"

    async def test_excludes_inactive_terms(self, db: AsyncSession):
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=None,
            term_ko="비활성용어",
            translations={"ja": "非活性"},
            category="general",
            is_active=False,
        ))
        await db.commit()

        result = await load_term_dict(db)
        assert "ja" not in result or "非活性" not in result.get("ja", {})

    async def test_empty_db_returns_empty_dict(self, db: AsyncSession):
        result = await load_term_dict(db)
        assert result == {}
