import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.query_utils import escape_like
from app.dependencies import get_current_user
from app.models.medical_term import MedicalTerm
from app.models.user import User
from app.schemas.medical_term import (
    MedicalTermCreate,
    MedicalTermResponse,
    MedicalTermUpdate,
)

router = APIRouter(prefix="/medical-terms", tags=["medical-terms"])


async def _get_term(
    db: AsyncSession, term_id: uuid.UUID, clinic_id: uuid.UUID
) -> MedicalTerm:
    result = await db.execute(
        select(MedicalTerm).where(
            MedicalTerm.id == term_id,
            or_(
                MedicalTerm.clinic_id == clinic_id,
                MedicalTerm.clinic_id.is_(None),
            ),
        )
    )
    term = result.scalar_one_or_none()
    if term is None:
        raise NotFoundError("Medical term not found")
    return term


@router.post("", response_model=MedicalTermResponse, status_code=201)
async def create_medical_term(
    body: MedicalTermCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    term = MedicalTerm(
        clinic_id=current_user.clinic_id,
        term_ko=body.term_ko,
        translations=body.translations,
        category=body.category,
        description=body.description,
    )
    db.add(term)
    await db.flush()
    return term


@router.get("", response_model=list[MedicalTermResponse])
async def list_medical_terms(
    category: str | None = Query(None),
    q: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(MedicalTerm).where(
        or_(
            MedicalTerm.clinic_id == current_user.clinic_id,
            MedicalTerm.clinic_id.is_(None),
        ),
        MedicalTerm.is_active.is_(True),
    )
    if category:
        query = query.where(MedicalTerm.category == category)
    if q:
        query = query.where(
            MedicalTerm.term_ko.ilike(f"%{escape_like(q)}%", escape="\\")
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{term_id}", response_model=MedicalTermResponse)
async def get_medical_term(
    term_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_term(db, term_id, current_user.clinic_id)


@router.patch("/{term_id}", response_model=MedicalTermResponse)
async def update_medical_term(
    term_id: uuid.UUID,
    body: MedicalTermUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    term = await _get_term(db, term_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(term, field, value)
    # Mark for re-indexing
    term.embedding = None
    await db.flush()
    return term


@router.delete("/{term_id}", status_code=204)
async def delete_medical_term(
    term_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    term = await _get_term(db, term_id, current_user.clinic_id)
    await db.delete(term)
    await db.flush()
