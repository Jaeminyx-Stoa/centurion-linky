import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.crm_event import CRMEvent
from app.models.followup_rule import FollowupRule
from app.models.side_effect_keyword import SideEffectKeyword
from app.models.user import User
from app.schemas.followup import (
    FollowupRuleCreate,
    FollowupRuleResponse,
    FollowupRuleUpdate,
    SideEffectAlertResponse,
    SideEffectKeywordCreate,
    SideEffectKeywordResponse,
)

router = APIRouter(prefix="/followups", tags=["followups"])


# --- Followup Rules ---


@router.post("/rules", response_model=FollowupRuleResponse, status_code=201)
async def create_followup_rule(
    body: FollowupRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = FollowupRule(
        id=uuid.uuid4(),
        clinic_id=current_user.clinic_id,
        procedure_id=body.procedure_id,
        event_type=body.event_type,
        delay_days=body.delay_days,
        delay_hours=body.delay_hours,
        message_template=body.message_template,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(rule)
    await db.flush()

    return await _load_rule_response(db, rule.id)


@router.get("/rules", response_model=list[FollowupRuleResponse])
async def list_followup_rules(
    procedure_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(FollowupRule)
        .options(selectinload(FollowupRule.procedure))
        .where(FollowupRule.clinic_id == current_user.clinic_id)
        .order_by(FollowupRule.sort_order)
    )
    if procedure_id is not None:
        query = query.where(FollowupRule.procedure_id == procedure_id)

    result = await db.execute(query)
    rules = result.scalars().all()

    return [_rule_to_response(r) for r in rules]


@router.get("/rules/{rule_id}", response_model=FollowupRuleResponse)
async def get_followup_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _load_rule_response(db, rule_id, current_user.clinic_id)


@router.patch("/rules/{rule_id}", response_model=FollowupRuleResponse)
async def update_followup_rule(
    rule_id: uuid.UUID,
    body: FollowupRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FollowupRule).where(
            FollowupRule.id == rule_id,
            FollowupRule.clinic_id == current_user.clinic_id,
        )
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        raise NotFoundError("Followup rule not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    await db.flush()

    return await _load_rule_response(db, rule.id)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_followup_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FollowupRule).where(
            FollowupRule.id == rule_id,
            FollowupRule.clinic_id == current_user.clinic_id,
        )
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        raise NotFoundError("Followup rule not found")
    await db.delete(rule)
    await db.flush()


# --- Side Effect Keywords ---


@router.post("/keywords", response_model=SideEffectKeywordResponse, status_code=201)
async def create_side_effect_keywords(
    body: SideEffectKeywordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kw = SideEffectKeyword(
        id=uuid.uuid4(),
        clinic_id=current_user.clinic_id,
        language=body.language,
        keywords=body.keywords,
        severity=body.severity,
    )
    db.add(kw)
    await db.flush()
    return kw


@router.get("/keywords", response_model=list[SideEffectKeywordResponse])
async def list_side_effect_keywords(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SideEffectKeyword).where(
            SideEffectKeyword.clinic_id == current_user.clinic_id,
        )
    )
    return list(result.scalars().all())


# --- Side Effect Alerts ---


@router.get("/alerts", response_model=list[SideEffectAlertResponse])
async def list_side_effect_alerts(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent side-effect alert CRM events."""
    from datetime import date, timedelta

    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(CRMEvent)
        .options(selectinload(CRMEvent.customer))
        .where(
            CRMEvent.clinic_id == current_user.clinic_id,
            CRMEvent.event_type == "side_effect_alert",
            func.date(CRMEvent.created_at) >= cutoff,
        )
        .order_by(CRMEvent.created_at.desc())
        .limit(50)
    )
    events = result.scalars().all()

    alerts = []
    for event in events:
        response_data = event.response or {}
        alerts.append(
            SideEffectAlertResponse(
                customer_id=event.customer_id,
                customer_name=event.customer.name if event.customer else None,
                conversation_id=response_data.get("conversation_id", event.booking_id or event.id),
                matched_keywords=response_data.get("matched_keywords", []),
                severity=response_data.get("severity", "normal"),
                message_preview=event.message_content or "",
                detected_at=event.created_at,
            )
        )
    return alerts


# --- Helpers ---


async def _load_rule_response(
    db: AsyncSession,
    rule_id: uuid.UUID,
    clinic_id: uuid.UUID | None = None,
) -> FollowupRuleResponse:
    query = (
        select(FollowupRule)
        .options(selectinload(FollowupRule.procedure))
        .where(FollowupRule.id == rule_id)
    )
    if clinic_id:
        query = query.where(FollowupRule.clinic_id == clinic_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    if rule is None:
        raise NotFoundError("Followup rule not found")
    return _rule_to_response(rule)


def _rule_to_response(rule: FollowupRule) -> FollowupRuleResponse:
    procedure_name = None
    if rule.procedure:
        procedure_name = getattr(rule.procedure, "name_ko", None) or str(rule.procedure_id)
    return FollowupRuleResponse(
        id=rule.id,
        clinic_id=rule.clinic_id,
        procedure_id=rule.procedure_id,
        procedure_name=procedure_name,
        event_type=rule.event_type,
        delay_days=rule.delay_days,
        delay_hours=rule.delay_hours,
        message_template=rule.message_template,
        is_active=rule.is_active,
        sort_order=rule.sort_order,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )
