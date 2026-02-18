import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.satisfaction.analyzer import SatisfactionAnalyzer, score_to_level
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.satisfaction_score import SatisfactionScore
from app.models.user import User
from app.schemas.satisfaction_score import (
    SatisfactionScoreResponse,
    SupervisorOverride,
)

router = APIRouter(prefix="/satisfaction", tags=["satisfaction"])

_analyzer = SatisfactionAnalyzer()


async def _get_score(
    db: AsyncSession, score_id: uuid.UUID, clinic_id: uuid.UUID
) -> SatisfactionScore:
    result = await db.execute(
        select(SatisfactionScore).where(
            SatisfactionScore.id == score_id,
            SatisfactionScore.clinic_id == clinic_id,
        )
    )
    score = result.scalar_one_or_none()
    if score is None:
        raise NotFoundError("Satisfaction score not found")
    return score


@router.post(
    "/analyze/{conversation_id}",
    response_model=SatisfactionScoreResponse,
    status_code=201,
)
async def analyze_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run satisfaction analysis on a conversation and save the score."""
    # Verify conversation belongs to clinic
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == current_user.clinic_id,
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation is None:
        raise NotFoundError("Conversation not found")

    # Get recent messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    messages = list(reversed(msg_result.scalars().all()))

    msg_dicts = [
        {
            "sender_type": m.sender_type,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in messages
    ]

    # Analyze
    result = _analyzer.analyze(msg_dicts)

    # Save score
    score = SatisfactionScore(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        clinic_id=current_user.clinic_id,
        score=result.score,
        level=result.level,
        language_signals=result.language_signals,
        behavior_signals=result.behavior_signals,
        flow_signals=result.flow_signals,
    )
    db.add(score)

    # Update conversation cache
    conversation.satisfaction_score = result.score
    conversation.satisfaction_level = result.level

    await db.flush()
    return score


@router.get(
    "/conversation/{conversation_id}",
    response_model=list[SatisfactionScoreResponse],
)
async def get_conversation_scores(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get satisfaction score history for a conversation."""
    result = await db.execute(
        select(SatisfactionScore)
        .where(
            SatisfactionScore.conversation_id == conversation_id,
            SatisfactionScore.clinic_id == current_user.clinic_id,
        )
        .order_by(SatisfactionScore.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{score_id}/override", response_model=SatisfactionScoreResponse)
async def supervisor_override(
    score_id: uuid.UUID,
    body: SupervisorOverride,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor overrides a satisfaction score."""
    score = await _get_score(db, score_id, current_user.clinic_id)

    score.supervisor_override = body.corrected_score
    score.supervisor_note = body.note
    score.supervised_by = current_user.id
    score.supervised_at = datetime.now(timezone.utc)

    # Update conversation cache with overridden score
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == score.conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation:
        conversation.satisfaction_score = body.corrected_score
        conversation.satisfaction_level = score_to_level(body.corrected_score)

    await db.flush()
    await db.refresh(score)
    return score


@router.get("/alerts", response_model=list[SatisfactionScoreResponse])
async def get_alerts(
    level: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get satisfaction scores that need attention (orange/red)."""
    stmt = select(SatisfactionScore).where(
        SatisfactionScore.clinic_id == current_user.clinic_id,
    )
    if level:
        stmt = stmt.where(SatisfactionScore.level == level)
    else:
        stmt = stmt.where(SatisfactionScore.level.in_(["orange", "red"]))
    stmt = stmt.order_by(SatisfactionScore.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
