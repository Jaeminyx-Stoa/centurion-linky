import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.ai_persona import AIPersona
from app.models.user import User
from app.schemas.ai_persona import (
    AIPersonaCreate,
    AIPersonaResponse,
    AIPersonaUpdate,
)

router = APIRouter(prefix="/ai-personas", tags=["ai-personas"])


async def _get_persona(
    db: AsyncSession, persona_id: uuid.UUID, clinic_id: uuid.UUID
) -> AIPersona:
    result = await db.execute(
        select(AIPersona).where(
            AIPersona.id == persona_id,
            AIPersona.clinic_id == clinic_id,
        )
    )
    persona = result.scalar_one_or_none()
    if persona is None:
        raise NotFoundError("AI persona not found")
    return persona


@router.post("", response_model=AIPersonaResponse, status_code=201)
async def create_persona(
    body: AIPersonaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = AIPersona(
        clinic_id=current_user.clinic_id,
        name=body.name,
        personality=body.personality,
        system_prompt=body.system_prompt,
        avatar_url=body.avatar_url,
        is_default=body.is_default,
    )
    db.add(persona)
    await db.flush()
    return persona


@router.get("", response_model=list[AIPersonaResponse])
async def list_personas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIPersona)
        .where(AIPersona.clinic_id == current_user.clinic_id)
        .order_by(AIPersona.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{persona_id}", response_model=AIPersonaResponse)
async def get_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_persona(db, persona_id, current_user.clinic_id)


@router.patch("/{persona_id}", response_model=AIPersonaResponse)
async def update_persona(
    persona_id: uuid.UUID,
    body: AIPersonaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = await _get_persona(db, persona_id, current_user.clinic_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)
    await db.flush()
    await db.refresh(persona)
    return persona


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = await _get_persona(db, persona_id, current_user.clinic_id)
    await db.delete(persona)
    await db.flush()
