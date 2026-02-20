import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.query_utils import escape_like
from app.dependencies import get_current_user
from app.models.procedure import Procedure
from app.models.user import User
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureResponse,
    ProcedureUpdate,
)

router = APIRouter(prefix="/procedures", tags=["procedures"])


async def _get_procedure(db: AsyncSession, procedure_id: uuid.UUID) -> Procedure:
    result = await db.execute(
        select(Procedure).where(Procedure.id == procedure_id)
    )
    proc = result.scalar_one_or_none()
    if proc is None:
        raise NotFoundError("Procedure not found")
    return proc


@router.post("", response_model=ProcedureResponse, status_code=201)
async def create_procedure(
    body: ProcedureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check slug uniqueness
    existing = await db.execute(
        select(Procedure).where(Procedure.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already exists")

    proc = Procedure(**body.model_dump())
    db.add(proc)
    await db.flush()
    return proc


@router.get("", response_model=list[ProcedureResponse])
async def list_procedures(
    category_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Procedure).where(Procedure.is_active.is_(True))
    if category_id:
        query = query.where(Procedure.category_id == category_id)
    if q:
        query = query.where(
            Procedure.name_ko.ilike(f"%{escape_like(q)}%", escape="\\")
        )
    query = query.order_by(Procedure.name_ko)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{procedure_id}", response_model=ProcedureResponse)
async def get_procedure(
    procedure_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_procedure(db, procedure_id)


@router.patch("/{procedure_id}", response_model=ProcedureResponse)
async def update_procedure(
    procedure_id: uuid.UUID,
    body: ProcedureUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    proc = await _get_procedure(db, procedure_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proc, field, value)
    await db.flush()
    await db.refresh(proc)
    return proc
