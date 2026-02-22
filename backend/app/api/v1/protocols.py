import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.pagination import paginate
from app.dependencies import get_current_user, get_pagination
from app.models.booking import Booking
from app.models.consultation_protocol import ConsultationProtocol
from app.models.user import User
from app.schemas.consultation_protocol import (
    ConsultationProtocolCreate,
    ConsultationProtocolResponse,
    ConsultationProtocolUpdate,
    ProtocolStateItemResponse,
    ProtocolStateResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/protocols", tags=["protocols"])


@router.post("", response_model=ConsultationProtocolResponse, status_code=201)
async def create_protocol(
    body: ConsultationProtocolCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    protocol = ConsultationProtocol(
        id=uuid.uuid4(),
        clinic_id=current_user.clinic_id,
        procedure_id=body.procedure_id,
        name=body.name,
        checklist_items=[item.model_dump() for item in body.checklist_items],
    )
    db.add(protocol)
    await db.flush()
    return protocol


@router.get("")
async def list_protocols(
    procedure_id: uuid.UUID | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ConsultationProtocolResponse]:
    stmt = (
        select(ConsultationProtocol)
        .where(ConsultationProtocol.clinic_id == current_user.clinic_id)
        .order_by(ConsultationProtocol.created_at.desc())
    )
    if procedure_id:
        stmt = stmt.where(ConsultationProtocol.procedure_id == procedure_id)
    return await paginate(db, stmt, pagination)


@router.get("/{protocol_id}", response_model=ConsultationProtocolResponse)
async def get_protocol(
    protocol_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConsultationProtocol).where(
            ConsultationProtocol.id == protocol_id,
            ConsultationProtocol.clinic_id == current_user.clinic_id,
        )
    )
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise NotFoundError("Protocol not found")
    return protocol


@router.patch("/{protocol_id}", response_model=ConsultationProtocolResponse)
async def update_protocol(
    protocol_id: uuid.UUID,
    body: ConsultationProtocolUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConsultationProtocol).where(
            ConsultationProtocol.id == protocol_id,
            ConsultationProtocol.clinic_id == current_user.clinic_id,
        )
    )
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise NotFoundError("Protocol not found")

    update_data = body.model_dump(exclude_unset=True)
    if "checklist_items" in update_data and update_data["checklist_items"] is not None:
        update_data["checklist_items"] = [
            item.model_dump() for item in body.checklist_items
        ]
    for field, value in update_data.items():
        setattr(protocol, field, value)
    await db.flush()
    return protocol


@router.get("/bookings/{booking_id}/state", response_model=ProtocolStateResponse)
async def get_protocol_state(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.clinic_id == current_user.clinic_id,
        )
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")

    state = booking.protocol_state or {}
    items = state.get("items", [])
    completed = sum(1 for i in items if i.get("answered"))

    return ProtocolStateResponse(
        protocol_id=uuid.UUID(state["protocol_id"]) if state.get("protocol_id") else uuid.uuid4(),
        total_items=len(items),
        completed_items=completed,
        is_complete=completed == len(items) and len(items) > 0,
        items=[
            ProtocolStateItemResponse(
                id=i["id"],
                answered=i.get("answered", False),
                answer=i.get("answer"),
            )
            for i in items
        ],
    )


@router.post("/bookings/{booking_id}/init")
async def init_protocol_state(
    booking_id: uuid.UUID,
    protocol_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load booking
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.clinic_id == current_user.clinic_id,
        )
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")

    # Load protocol
    proto_result = await db.execute(
        select(ConsultationProtocol).where(
            ConsultationProtocol.id == protocol_id,
            ConsultationProtocol.clinic_id == current_user.clinic_id,
        )
    )
    protocol = proto_result.scalar_one_or_none()
    if protocol is None:
        raise NotFoundError("Protocol not found")

    checklist = protocol.checklist_items or []
    booking.protocol_state = {
        "protocol_id": str(protocol_id),
        "items": [
            {"id": item["id"], "answered": False, "answer": None}
            for item in checklist
        ],
    }
    await db.flush()
    return {"status": "ok", "total_items": len(checklist)}


@router.patch("/bookings/{booking_id}/items/{item_id}")
async def update_protocol_item(
    booking_id: uuid.UUID,
    item_id: str,
    answer: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.clinic_id == current_user.clinic_id,
        )
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")

    state = booking.protocol_state or {}
    items = state.get("items", [])

    updated = False
    for item in items:
        if item["id"] == item_id:
            item["answered"] = True
            item["answer"] = answer
            updated = True
            break

    if not updated:
        raise NotFoundError("Checklist item not found")

    booking.protocol_state = state
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(booking, "protocol_state")
    await db.flush()

    completed = sum(1 for i in items if i.get("answered"))
    return {
        "status": "ok",
        "item_id": item_id,
        "completed_items": completed,
        "total_items": len(items),
        "is_complete": completed == len(items),
    }
