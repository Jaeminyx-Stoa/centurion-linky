import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cultural_profile import CulturalProfile
from app.models.medical_term import MedicalTerm
from app.seeds.cultural_profiles import CULTURAL_PROFILES, MEDICAL_TERMS_SEED
from app.seeds.runner import run_all_seeds, seed_cultural_profiles, seed_medical_terms


class TestSeedCulturalProfiles:
    async def test_creates_all_profiles(self, db: AsyncSession):
        count = await seed_cultural_profiles(db)
        await db.commit()

        assert count == len(CULTURAL_PROFILES)

        result = await db.execute(select(CulturalProfile))
        profiles = result.scalars().all()
        assert len(profiles) == len(CULTURAL_PROFILES)

        codes = {p.country_code for p in profiles}
        assert "JP" in codes
        assert "CN" in codes
        assert "TW" in codes
        assert "US" in codes
        assert "VN" in codes
        assert "TH" in codes
        assert "ID" in codes

    async def test_idempotent_on_rerun(self, db: AsyncSession):
        await seed_cultural_profiles(db)
        await db.commit()

        # Run again
        count = await seed_cultural_profiles(db)
        await db.commit()

        assert count == len(CULTURAL_PROFILES)

        result = await db.execute(select(CulturalProfile))
        assert len(result.scalars().all()) == len(CULTURAL_PROFILES)

    async def test_jp_profile_has_correct_values(self, db: AsyncSession):
        await seed_cultural_profiles(db)
        await db.commit()

        result = await db.execute(
            select(CulturalProfile).where(CulturalProfile.country_code == "JP")
        )
        jp = result.scalar_one()
        assert jp.language_code == "ja"
        assert jp.formality_level == "formal"
        assert jp.emoji_level == "low"


class TestSeedMedicalTerms:
    async def test_creates_all_terms(self, db: AsyncSession):
        count = await seed_medical_terms(db)
        await db.commit()

        assert count == len(MEDICAL_TERMS_SEED)

        result = await db.execute(
            select(MedicalTerm).where(MedicalTerm.clinic_id.is_(None))
        )
        terms = result.scalars().all()
        assert len(terms) == len(MEDICAL_TERMS_SEED)

    async def test_botox_has_all_translations(self, db: AsyncSession):
        await seed_medical_terms(db)
        await db.commit()

        result = await db.execute(
            select(MedicalTerm).where(MedicalTerm.term_ko == "보톡스")
        )
        botox = result.scalar_one()
        assert botox.translations["ja"] == "ボトックス"
        assert botox.translations["en"] == "Botox"
        assert botox.translations["zh-CN"] == "肉毒素"

    async def test_idempotent_on_rerun(self, db: AsyncSession):
        await seed_medical_terms(db)
        await db.commit()

        await seed_medical_terms(db)
        await db.commit()

        result = await db.execute(
            select(MedicalTerm).where(MedicalTerm.clinic_id.is_(None))
        )
        assert len(result.scalars().all()) == len(MEDICAL_TERMS_SEED)


class TestRunAllSeeds:
    async def test_run_all(self, db: AsyncSession):
        counts = await run_all_seeds(db)
        await db.commit()

        assert counts["cultural_profiles"] == len(CULTURAL_PROFILES)
        assert counts["medical_terms"] == len(MEDICAL_TERMS_SEED)
