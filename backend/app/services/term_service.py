"""Loads medical terms from DB into the dict format needed by TranslationChain."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_term import MedicalTerm


async def load_term_dict(
    db: AsyncSession,
    clinic_id=None,
) -> dict[str, dict[str, str]]:
    """Build {language_code: {foreign_term: korean_term}} from active MedicalTerms.

    Includes global terms (clinic_id=None) and optionally clinic-specific terms.
    Clinic terms override globals when there's a conflict.
    """
    from sqlalchemy import or_

    filters = [MedicalTerm.is_active.is_(True)]
    if clinic_id:
        filters.append(or_(
            MedicalTerm.clinic_id.is_(None),
            MedicalTerm.clinic_id == clinic_id,
        ))
    else:
        filters.append(MedicalTerm.clinic_id.is_(None))

    result = await db.execute(
        select(MedicalTerm).where(*filters).order_by(
            MedicalTerm.clinic_id.asc().nulls_first()
        )
    )
    terms = result.scalars().all()

    term_dict: dict[str, dict[str, str]] = {}
    for term in terms:
        for lang_code, foreign_text in term.translations.items():
            if lang_code not in term_dict:
                term_dict[lang_code] = {}
            term_dict[lang_code][foreign_text] = term.term_ko

    return term_dict
