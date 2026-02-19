from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.clinic import Clinic
from app.models.user import User
from app.schemas.clinic import ClinicResponse, ClinicSettingsUpdate, ClinicUpdate

router = APIRouter(prefix="/clinics", tags=["clinics"])


async def _get_clinic(db: AsyncSession, clinic_id) -> Clinic:
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()
    if clinic is None:
        raise NotFoundError("Clinic not found")
    return clinic


@router.get("/me", response_model=ClinicResponse)
async def get_my_clinic(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_clinic(db, current_user.clinic_id)


@router.patch("/me", response_model=ClinicResponse)
async def update_my_clinic(
    body: ClinicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clinic = await _get_clinic(db, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clinic, field, value)
    await db.flush()
    await db.refresh(clinic)
    return clinic


@router.patch("/me/settings", response_model=ClinicResponse)
async def update_my_clinic_settings(
    body: ClinicSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clinic = await _get_clinic(db, current_user.clinic_id)
    # Merge-update: keep existing keys, update/add new ones
    current_settings = dict(clinic.settings) if clinic.settings else {}
    current_settings.update(body.settings)
    clinic.settings = current_settings
    await db.flush()
    await db.refresh(clinic)
    return clinic
