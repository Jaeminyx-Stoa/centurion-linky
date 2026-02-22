import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.query_utils import escape_like
from app.dependencies import get_current_user
from app.models.response_library import ResponseLibrary
from app.models.user import User
from app.schemas.response_library import (
    ResponseLibraryCreate,
    ResponseLibraryResponse,
    ResponseLibraryUpdate,
)

router = APIRouter(prefix="/response-library", tags=["response-library"])


async def _get_entry(
    db: AsyncSession, entry_id: uuid.UUID, clinic_id: uuid.UUID
) -> ResponseLibrary:
    result = await db.execute(
        select(ResponseLibrary).where(
            ResponseLibrary.id == entry_id,
            ResponseLibrary.clinic_id == clinic_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError("Response library entry not found")
    return entry


@router.post("", response_model=ResponseLibraryResponse, status_code=201)
async def create_response_library(
    body: ResponseLibraryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = ResponseLibrary(
        clinic_id=current_user.clinic_id,
        category=body.category,
        question=body.question,
        answer=body.answer,
        subcategory=body.subcategory,
        language_code=body.language_code,
        tags=body.tags,
    )
    db.add(entry)
    await db.flush()
    return entry


@router.get("", response_model=list[ResponseLibraryResponse])
async def list_response_library(
    category: str | None = Query(None),
    q: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ResponseLibrary).where(
        ResponseLibrary.clinic_id == current_user.clinic_id,
        ResponseLibrary.is_active.is_(True),
    )
    if category:
        query = query.where(ResponseLibrary.category == category)
    if q:
        query = query.where(
            ResponseLibrary.question.ilike(f"%{escape_like(q)}%", escape="\\")
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{entry_id}", response_model=ResponseLibraryResponse)
async def get_response_library(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_entry(db, entry_id, current_user.clinic_id)


@router.patch("/{entry_id}", response_model=ResponseLibraryResponse)
async def update_response_library(
    entry_id: uuid.UUID,
    body: ResponseLibraryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_entry(db, entry_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    # Mark for re-indexing
    entry.embedding = None
    await db.flush()
    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_response_library(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_entry(db, entry_id, current_user.clinic_id)
    await db.delete(entry)
    await db.flush()
