import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.dependencies import get_current_user
from app.models.crm_event import CRMEvent
from app.models.satisfaction_survey import SatisfactionSurvey
from app.models.user import User
from app.schemas.crm_event import CRMEventResponse
from app.schemas.satisfaction_survey import (
    CRMDashboardResponse,
    SatisfactionSurveyCreate,
    SatisfactionSurveyResponse,
    SurveySummaryResponse,
)

router = APIRouter(prefix="/crm", tags=["crm"])


# --- Helper ---
async def _get_event(
    db: AsyncSession, event_id: uuid.UUID, clinic_id: uuid.UUID
) -> CRMEvent:
    result = await db.execute(
        select(CRMEvent).where(
            CRMEvent.id == event_id,
            CRMEvent.clinic_id == clinic_id,
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise NotFoundError("CRM event not found")
    return event


# ==================== CRM Events ====================

@router.get("/events", response_model=list[CRMEventResponse])
async def list_events(
    status: str | None = Query(None),
    event_type: str | None = Query(None),
    customer_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMEvent).where(CRMEvent.clinic_id == current_user.clinic_id)
    if status:
        stmt = stmt.where(CRMEvent.status == status)
    if event_type:
        stmt = stmt.where(CRMEvent.event_type == event_type)
    if customer_id:
        stmt = stmt.where(CRMEvent.customer_id == customer_id)
    stmt = stmt.order_by(CRMEvent.scheduled_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/events/{event_id}", response_model=CRMEventResponse)
async def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_event(db, event_id, current_user.clinic_id)


@router.post("/events/{event_id}/cancel", response_model=CRMEventResponse)
async def cancel_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event = await _get_event(db, event_id, current_user.clinic_id)
    if event.status != "scheduled":
        raise BadRequestError(
            f"Cannot cancel event with status '{event.status}'"
        )
    event.status = "cancelled"
    await db.flush()
    await db.refresh(event)
    return event


# ==================== Surveys ====================

@router.get("/surveys", response_model=list[SatisfactionSurveyResponse])
async def list_surveys(
    survey_round: int | None = Query(None, ge=1, le=3),
    customer_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SatisfactionSurvey).where(
        SatisfactionSurvey.clinic_id == current_user.clinic_id
    )
    if survey_round:
        stmt = stmt.where(SatisfactionSurvey.survey_round == survey_round)
    if customer_id:
        stmt = stmt.where(SatisfactionSurvey.customer_id == customer_id)
    stmt = stmt.order_by(SatisfactionSurvey.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/surveys", response_model=SatisfactionSurveyResponse, status_code=201)
async def create_survey(
    body: SatisfactionSurveyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    survey = SatisfactionSurvey(
        clinic_id=current_user.clinic_id,
        customer_id=body.customer_id,
        booking_id=body.booking_id,
        crm_event_id=body.crm_event_id,
        survey_round=body.survey_round,
        satisfaction_score=body.satisfaction_score,
        revisit_intention=body.revisit_intention,
        nps_score=body.nps_score,
        feedback_text=body.feedback_text,
        side_effects_reported=body.side_effects_reported,
        responded_at=datetime.now(timezone.utc),
    )
    db.add(survey)
    await db.flush()
    return survey


@router.get("/surveys/summary", response_model=SurveySummaryResponse)
async def survey_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clinic_id = current_user.clinic_id

    # Total + averages
    total_result = await db.execute(
        select(
            func.count(SatisfactionSurvey.id),
            func.avg(SatisfactionSurvey.satisfaction_score),
            func.avg(SatisfactionSurvey.nps_score),
        ).where(SatisfactionSurvey.clinic_id == clinic_id)
    )
    total_row = total_result.one()
    total_surveys = total_row[0]
    avg_satisfaction = round(float(total_row[1]), 2) if total_row[1] else None
    avg_nps = round(float(total_row[2]), 2) if total_row[2] else None

    # Revisit yes percentage
    revisit_result = await db.execute(
        select(
            func.count(SatisfactionSurvey.id),
        ).where(
            SatisfactionSurvey.clinic_id == clinic_id,
            SatisfactionSurvey.revisit_intention == "yes",
        )
    )
    revisit_yes_count = revisit_result.scalar()
    revisit_total_result = await db.execute(
        select(
            func.count(SatisfactionSurvey.id),
        ).where(
            SatisfactionSurvey.clinic_id == clinic_id,
            SatisfactionSurvey.revisit_intention.isnot(None),
        )
    )
    revisit_total = revisit_total_result.scalar()
    revisit_yes_pct = (
        round(revisit_yes_count / revisit_total * 100, 1)
        if revisit_total
        else None
    )

    # By round
    by_round = {}
    for r in (1, 2, 3):
        round_result = await db.execute(
            select(
                func.count(SatisfactionSurvey.id),
                func.avg(SatisfactionSurvey.satisfaction_score),
            ).where(
                SatisfactionSurvey.clinic_id == clinic_id,
                SatisfactionSurvey.survey_round == r,
            )
        )
        row = round_result.one()
        by_round[r] = {
            "count": row[0],
            "avg_score": round(float(row[1]), 2) if row[1] else None,
        }

    return SurveySummaryResponse(
        total_surveys=total_surveys,
        avg_satisfaction=avg_satisfaction,
        avg_nps=avg_nps,
        revisit_yes_pct=revisit_yes_pct,
        by_round=by_round,
    )


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=CRMDashboardResponse)
async def crm_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clinic_id = current_user.clinic_id

    # Event counts by status
    event_result = await db.execute(
        select(
            CRMEvent.status,
            func.count(CRMEvent.id),
        )
        .where(CRMEvent.clinic_id == clinic_id)
        .group_by(CRMEvent.status)
    )
    status_counts = dict(event_result.all())
    total_events = sum(status_counts.values())

    # Survey aggregates
    survey_result = await db.execute(
        select(
            func.count(SatisfactionSurvey.id),
            func.avg(SatisfactionSurvey.satisfaction_score),
            func.avg(SatisfactionSurvey.nps_score),
        ).where(SatisfactionSurvey.clinic_id == clinic_id)
    )
    survey_row = survey_result.one()

    return CRMDashboardResponse(
        total_events=total_events,
        scheduled=status_counts.get("scheduled", 0),
        sent=status_counts.get("sent", 0),
        completed=status_counts.get("completed", 0),
        cancelled=status_counts.get("cancelled", 0),
        failed=status_counts.get("failed", 0),
        total_surveys=survey_row[0],
        avg_satisfaction=round(float(survey_row[1]), 2) if survey_row[1] else None,
        avg_nps=round(float(survey_row[2]), 2) if survey_row[2] else None,
    )


@router.get("/satisfaction-trend")
async def satisfaction_trend(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Satisfaction trend by survey round."""
    clinic_id = current_user.clinic_id
    result = await db.execute(
        select(
            SatisfactionSurvey.survey_round,
            func.count(SatisfactionSurvey.id),
            func.avg(SatisfactionSurvey.satisfaction_score),
        )
        .where(SatisfactionSurvey.clinic_id == clinic_id)
        .group_by(SatisfactionSurvey.survey_round)
        .order_by(SatisfactionSurvey.survey_round)
    )
    rows = result.all()
    return [
        {
            "round": row[0],
            "count": row[1],
            "avg_score": round(float(row[2]), 2) if row[2] else None,
        }
        for row in rows
    ]


@router.get("/nps")
async def nps_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """NPS breakdown: promoters (9-10), passives (7-8), detractors (0-6)."""
    clinic_id = current_user.clinic_id

    # Get all NPS scores
    result = await db.execute(
        select(SatisfactionSurvey.nps_score).where(
            SatisfactionSurvey.clinic_id == clinic_id,
            SatisfactionSurvey.nps_score.isnot(None),
        )
    )
    scores = [row[0] for row in result.all()]

    if not scores:
        return {"promoters": 0, "passives": 0, "detractors": 0, "nps": None, "total": 0}

    total = len(scores)
    promoters = sum(1 for s in scores if s >= 9)
    passives = sum(1 for s in scores if 7 <= s <= 8)
    detractors = sum(1 for s in scores if s <= 6)
    nps = round((promoters - detractors) / total * 100, 1)

    return {
        "promoters": promoters,
        "passives": passives,
        "detractors": detractors,
        "nps": nps,
        "total": total,
    }


@router.get("/revisit-rate")
async def revisit_rate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revisit intention breakdown."""
    clinic_id = current_user.clinic_id

    result = await db.execute(
        select(
            SatisfactionSurvey.revisit_intention,
            func.count(SatisfactionSurvey.id),
        )
        .where(
            SatisfactionSurvey.clinic_id == clinic_id,
            SatisfactionSurvey.revisit_intention.isnot(None),
        )
        .group_by(SatisfactionSurvey.revisit_intention)
    )
    counts = dict(result.all())
    total = sum(counts.values())

    return {
        "yes": counts.get("yes", 0),
        "maybe": counts.get("maybe", 0),
        "no": counts.get("no", 0),
        "total": total,
        "yes_rate": round(counts.get("yes", 0) / total * 100, 1) if total else None,
    }
