from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic_procedure import ClinicProcedure
from app.models.procedure import Procedure


# Fields that can be customized by clinics
MERGE_FIELDS = [
    "description",
    "effects",
    "duration_minutes",
    "effect_duration",
    "downtime_days",
    "min_interval_days",
    "precautions_before",
    "precautions_during",
    "precautions_after",
    "pain_level",
    "anesthesia_options",
]


async def get_merged_procedure(
    db: AsyncSession,
    clinic_procedure: ClinicProcedure,
) -> dict:
    """Merge textbook defaults + clinic customizations."""
    result = await db.execute(
        select(Procedure).where(Procedure.id == clinic_procedure.procedure_id)
    )
    base = result.scalar_one()

    merged = {
        "id": clinic_procedure.id,
        "clinic_id": clinic_procedure.clinic_id,
        "procedure_id": clinic_procedure.procedure_id,
        "procedure_name_ko": base.name_ko,
        "procedure_slug": base.slug,
        "category_id": base.category_id,
        "material_cost": clinic_procedure.material_cost,
        "difficulty_score": clinic_procedure.difficulty_score,
        "clinic_preference": clinic_procedure.clinic_preference,
        "sales_performance_score": clinic_procedure.sales_performance_score,
        "is_active": clinic_procedure.is_active,
    }

    # Map merge field names to base procedure column names
    base_field_map = {
        "description": "description_ko",
        "effects": "effects_ko",
    }

    for field in MERGE_FIELDS:
        custom_value = getattr(clinic_procedure, f"custom_{field}")
        base_attr = base_field_map.get(field, field)
        base_value = getattr(base, base_attr)

        merged[field] = {
            "value": custom_value if custom_value is not None else base_value,
            "source": "custom" if custom_value is not None else "default",
            "default_value": base_value,
        }

    return merged
