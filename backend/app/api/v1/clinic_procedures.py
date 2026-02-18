import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.clinic_procedure import ClinicProcedure
from app.models.user import User
from app.schemas.clinic_procedure import (
    ClinicProcedureCreate,
    ClinicProcedureMergedResponse,
    ClinicProcedureResponse,
    ClinicProcedureUpdate,
)
from app.services.procedure_service import MERGE_FIELDS, get_merged_procedure

router = APIRouter(prefix="/clinic-procedures", tags=["clinic-procedures"])


async def _get_clinic_procedure(
    db: AsyncSession, cp_id: uuid.UUID, clinic_id: uuid.UUID
) -> ClinicProcedure:
    result = await db.execute(
        select(ClinicProcedure).where(
            ClinicProcedure.id == cp_id,
            ClinicProcedure.clinic_id == clinic_id,
        )
    )
    cp = result.scalar_one_or_none()
    if cp is None:
        raise NotFoundError("Clinic procedure not found")
    return cp


@router.post("", response_model=ClinicProcedureResponse, status_code=201)
async def create_clinic_procedure(
    body: ClinicProcedureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check uniqueness
    existing = await db.execute(
        select(ClinicProcedure).where(
            ClinicProcedure.clinic_id == current_user.clinic_id,
            ClinicProcedure.procedure_id == body.procedure_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Procedure already added to clinic")

    cp = ClinicProcedure(
        clinic_id=current_user.clinic_id,
        **body.model_dump(),
    )
    db.add(cp)
    await db.flush()
    return cp


@router.get("", response_model=list[ClinicProcedureResponse])
async def list_clinic_procedures(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClinicProcedure).where(
            ClinicProcedure.clinic_id == current_user.clinic_id,
            ClinicProcedure.is_active.is_(True),
        )
    )
    return result.scalars().all()


@router.get("/{cp_id}", response_model=ClinicProcedureMergedResponse)
async def get_clinic_procedure_merged(
    cp_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cp = await _get_clinic_procedure(db, cp_id, current_user.clinic_id)
    return await get_merged_procedure(db, cp)


@router.patch("/{cp_id}", response_model=ClinicProcedureResponse)
async def update_clinic_procedure(
    cp_id: uuid.UUID,
    body: ClinicProcedureUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cp = await _get_clinic_procedure(db, cp_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cp, field, value)
    await db.flush()
    await db.refresh(cp)
    return cp


@router.post("/{cp_id}/reset/{field_name}")
async def reset_field_to_default(
    cp_id: uuid.UUID,
    field_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if field_name not in MERGE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid field: {field_name}")

    cp = await _get_clinic_procedure(db, cp_id, current_user.clinic_id)
    setattr(cp, f"custom_{field_name}", None)
    await db.flush()
    return await get_merged_procedure(db, cp)


@router.delete("/{cp_id}", status_code=204)
async def delete_clinic_procedure(
    cp_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cp = await _get_clinic_procedure(db, cp_id, current_user.clinic_id)
    cp.is_active = False
    await db.flush()
