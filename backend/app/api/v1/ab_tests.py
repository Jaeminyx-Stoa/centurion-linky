import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.ab_test_engine import ABTestEngine
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.ab_test import ABTest, ABTestVariant
from app.models.user import User
from app.schemas.ab_test import (
    ABTestCreate,
    ABTestResponse,
    ABTestResultCreate,
    ABTestResultResponse,
    ABTestStatsResponse,
    ABTestUpdate,
)

router = APIRouter(prefix="/ab-tests", tags=["ab-tests"])


async def _get_test(
    db: AsyncSession, test_id: uuid.UUID, clinic_id: uuid.UUID
) -> ABTest:
    result = await db.execute(
        select(ABTest)
        .where(ABTest.id == test_id, ABTest.clinic_id == clinic_id)
        .options(selectinload(ABTest.variants))
    )
    test = result.scalar_one_or_none()
    if test is None:
        raise NotFoundError("A/B test not found")
    return test


@router.post("", response_model=ABTestResponse, status_code=201)
async def create_test(
    body: ABTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    test = ABTest(
        clinic_id=current_user.clinic_id,
        name=body.name,
        description=body.description,
        test_type=body.test_type,
        status="draft",
    )
    db.add(test)
    await db.flush()

    for v in body.variants:
        variant = ABTestVariant(
            ab_test_id=test.id,
            name=v.name,
            config=v.config,
            weight=v.weight,
        )
        db.add(variant)
    await db.flush()

    # Reload with variants
    return await _get_test(db, test.id, current_user.clinic_id)


@router.get("", response_model=list[ABTestResponse])
async def list_tests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ABTest)
        .where(ABTest.clinic_id == current_user.clinic_id)
        .options(selectinload(ABTest.variants))
        .order_by(ABTest.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{test_id}", response_model=ABTestResponse)
async def get_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_test(db, test_id, current_user.clinic_id)


@router.patch("/{test_id}", response_model=ABTestResponse)
async def update_test(
    test_id: uuid.UUID,
    body: ABTestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    test = await _get_test(db, test_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)

    # Handle activation
    if update_data.get("is_active") and not test.is_active:
        update_data["started_at"] = datetime.now(timezone.utc)
        update_data["status"] = "active"
    elif update_data.get("is_active") is False and test.is_active:
        update_data["ended_at"] = datetime.now(timezone.utc)
        update_data["status"] = "completed"

    for field, value in update_data.items():
        setattr(test, field, value)
    await db.flush()
    await db.refresh(test)
    return await _get_test(db, test.id, current_user.clinic_id)


@router.post(
    "/{test_id}/results",
    response_model=ABTestResultResponse,
    status_code=201,
)
async def record_result(
    test_id: uuid.UUID,
    body: ABTestResultCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify test exists
    await _get_test(db, test_id, current_user.clinic_id)

    engine = ABTestEngine(db)
    result = await engine.record_outcome(
        test_id=test_id,
        variant_id=body.variant_id,
        conversation_id=body.conversation_id,
        outcome=body.outcome,
        outcome_data=body.outcome_data,
    )
    return result


@router.get("/{test_id}/stats", response_model=list[ABTestStatsResponse])
async def get_stats(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify test exists
    await _get_test(db, test_id, current_user.clinic_id)

    engine = ABTestEngine(db)
    return await engine.get_stats(test_id)
