import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.simulation_engine import CUSTOMER_PERSONAS, analyze_simulation
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.simulation import SimulationResult, SimulationSession
from app.models.user import User
from app.schemas.simulation import (
    PersonaResponse,
    SimulationSessionCreate,
    SimulationSessionResponse,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.get("/personas", response_model=list[PersonaResponse])
async def list_personas():
    """List available customer personas for simulation."""
    return CUSTOMER_PERSONAS


@router.post("", response_model=SimulationSessionResponse, status_code=201)
async def create_session(
    body: SimulationSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new simulation session (pending state)."""
    session = SimulationSession(
        clinic_id=current_user.clinic_id,
        persona_name=body.persona_name,
        persona_config=body.persona_config,
        max_rounds=body.max_rounds,
        status="pending",
    )
    db.add(session)
    await db.flush()

    # Reload with result relationship
    reload = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session.id)
        .options(selectinload(SimulationSession.result))
    )
    return reload.scalar_one()


@router.get("", response_model=list[SimulationSessionResponse])
async def list_sessions(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SimulationSession)
        .where(SimulationSession.clinic_id == current_user.clinic_id)
        .options(selectinload(SimulationSession.result))
        .order_by(SimulationSession.created_at.desc())
    )
    if status:
        stmt = stmt.where(SimulationSession.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{session_id}", response_model=SimulationSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(
            SimulationSession.id == session_id,
            SimulationSession.clinic_id == current_user.clinic_id,
        )
        .options(selectinload(SimulationSession.result))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Simulation session not found")
    return session


@router.post("/{session_id}/complete", response_model=SimulationSessionResponse)
async def complete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a simulation as completed and generate result analysis."""
    result = await db.execute(
        select(SimulationSession)
        .where(
            SimulationSession.id == session_id,
            SimulationSession.clinic_id == current_user.clinic_id,
        )
        .options(selectinload(SimulationSession.result))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Simulation session not found")

    # Analyze messages
    analysis = analyze_simulation(session.messages or [])

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    session.actual_rounds = analysis["total_rounds"]

    # Create result
    sim_result = SimulationResult(
        session_id=session.id,
        clinic_id=current_user.clinic_id,
        booked=analysis["booked"],
        abandoned=analysis["abandoned"],
        satisfaction_score=analysis["satisfaction_estimate"],
        exit_reason=analysis["exit_reason"],
    )
    db.add(sim_result)
    await db.flush()
    await db.refresh(session)

    # Reload with result
    reload = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id)
        .options(selectinload(SimulationSession.result))
    )
    return reload.scalar_one()
