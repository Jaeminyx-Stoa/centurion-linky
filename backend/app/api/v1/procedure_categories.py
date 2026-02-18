import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.procedure_category import ProcedureCategory
from app.models.user import User
from app.schemas.procedure_category import (
    ProcedureCategoryCreate,
    ProcedureCategoryResponse,
    ProcedureCategoryTreeResponse,
    ProcedureCategoryUpdate,
)

router = APIRouter(prefix="/procedure-categories", tags=["procedure-categories"])


async def _get_category(db: AsyncSession, category_id: uuid.UUID) -> ProcedureCategory:
    result = await db.execute(
        select(ProcedureCategory).where(ProcedureCategory.id == category_id)
    )
    cat = result.scalar_one_or_none()
    if cat is None:
        raise NotFoundError("Procedure category not found")
    return cat


def _build_tree(
    categories: list[ProcedureCategory],
) -> list[dict]:
    by_id = {c.id: c for c in categories}
    tree: list[dict] = []

    for cat in categories:
        node = ProcedureCategoryResponse.model_validate(cat).model_dump()
        node["children"] = []
        by_id[cat.id] = node  # type: ignore[assignment]

    for cat in categories:
        node = by_id[cat.id]
        if cat.parent_id and cat.parent_id in by_id:
            parent_node = by_id[cat.parent_id]
            parent_node["children"].append(node)  # type: ignore[union-attr]
        else:
            tree.append(node)  # type: ignore[arg-type]

    return tree


@router.post("", response_model=ProcedureCategoryResponse, status_code=201)
async def create_procedure_category(
    body: ProcedureCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check slug uniqueness
    existing = await db.execute(
        select(ProcedureCategory).where(ProcedureCategory.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already exists")

    cat = ProcedureCategory(
        name_ko=body.name_ko,
        name_en=body.name_en,
        name_ja=body.name_ja,
        name_zh=body.name_zh,
        slug=body.slug,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
    )
    db.add(cat)
    await db.flush()
    return cat


@router.get("")
async def list_procedure_categories(
    flat: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcedureCategory).order_by(
            ProcedureCategory.sort_order, ProcedureCategory.name_ko
        )
    )
    categories = list(result.scalars().all())

    if flat:
        return [
            ProcedureCategoryResponse.model_validate(c).model_dump()
            for c in categories
        ]

    return _build_tree(categories)


@router.get("/{category_id}", response_model=ProcedureCategoryResponse)
async def get_procedure_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_category(db, category_id)


@router.patch("/{category_id}", response_model=ProcedureCategoryResponse)
async def update_procedure_category(
    category_id: uuid.UUID,
    body: ProcedureCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cat = await _get_category(db, category_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cat, field, value)
    await db.flush()
    return cat
