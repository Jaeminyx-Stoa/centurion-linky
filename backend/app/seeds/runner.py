"""Seed data runner — upserts cultural profiles and medical terms."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cultural_profile import CulturalProfile
from app.models.medical_term import MedicalTerm
from app.seeds.cultural_profiles import CULTURAL_PROFILES, MEDICAL_TERMS_SEED


async def seed_cultural_profiles(db: AsyncSession) -> int:
    """Upsert cultural profiles. Returns count of created/updated."""
    count = 0
    for data in CULTURAL_PROFILES:
        result = await db.execute(
            select(CulturalProfile).where(
                CulturalProfile.country_code == data["country_code"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            db.add(CulturalProfile(id=uuid.uuid4(), **data))
            count += 1
        else:
            for key, value in data.items():
                setattr(existing, key, value)
            count += 1

    await db.flush()
    return count


async def seed_medical_terms(db: AsyncSession) -> int:
    """Upsert global medical terms. Returns count of created/updated."""
    count = 0
    for data in MEDICAL_TERMS_SEED:
        result = await db.execute(
            select(MedicalTerm).where(
                MedicalTerm.term_ko == data["term_ko"],
                MedicalTerm.clinic_id.is_(None),
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            db.add(MedicalTerm(id=uuid.uuid4(), clinic_id=None, **data))
            count += 1
        else:
            for key, value in data.items():
                setattr(existing, key, value)
            count += 1

    await db.flush()
    return count


async def run_all_seeds(db: AsyncSession) -> dict[str, int]:
    """Run all seeds. Returns counts."""
    profiles = await seed_cultural_profiles(db)
    terms = await seed_medical_terms(db)
    return {"cultural_profiles": profiles, "medical_terms": terms}
