import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_pagination
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    MessageResponse,
    SendMessageRequest,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services.audit_service import log_action

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def _get_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, clinic_id: uuid.UUID
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == clinic_id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise NotFoundError("Conversation not found")
    return conv


@router.get("")
async def list_conversations(
    status: str | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ConversationListResponse]:
    base_query = select(Conversation).where(
        Conversation.clinic_id == current_user.clinic_id,
    )
    if status:
        base_query = base_query.where(Conversation.status == status)

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch page with eager loading to avoid N+1
    query = (
        base_query.options(
            selectinload(Conversation.customer),
            selectinload(Conversation.messenger_account),
        )
        .order_by(Conversation.last_message_at.desc().nulls_last())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    result = await db.execute(query)
    conversations = result.scalars().all()

    items = []
    for conv in conversations:
        customer = conv.customer
        account = conv.messenger_account
        items.append(ConversationListResponse(
            id=conv.id,
            clinic_id=conv.clinic_id,
            customer_id=conv.customer_id,
            messenger_account_id=conv.messenger_account_id,
            status=conv.status,
            ai_mode=conv.ai_mode,
            satisfaction_score=conv.satisfaction_score,
            satisfaction_level=conv.satisfaction_level,
            last_message_at=conv.last_message_at,
            last_message_preview=conv.last_message_preview,
            unread_count=conv.unread_count,
            created_at=conv.created_at,
            customer_name=customer.display_name or customer.name,
            customer_country=customer.country_code,
            customer_language=customer.language_code,
            messenger_type=account.messenger_type,
        ))
    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_conversation(db, conversation_id, current_user.clinic_id)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_conversation(db, conversation_id, current_user.clinic_id)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    # Mark as read
    conv.unread_count = 0
    await db.flush()

    return messages


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=201,
)
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_conversation(db, conversation_id, current_user.clinic_id)

    message = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        clinic_id=conv.clinic_id,
        sender_type="staff",
        sender_id=current_user.id,
        content=body.content,
        content_type="text",
    )
    db.add(message)
    await db.flush()
    return message


@router.post("/{conversation_id}/toggle-ai", response_model=ConversationDetailResponse)
async def toggle_ai(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_conversation(db, conversation_id, current_user.clinic_id)
    old_mode = conv.ai_mode
    conv.ai_mode = not conv.ai_mode
    if not conv.ai_mode:
        conv.assigned_to = current_user.id
    else:
        conv.assigned_to = None
    await log_action(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="toggle_ai",
        resource_type="conversation",
        resource_id=str(conv.id),
        changes={"ai_mode": {"old": old_mode, "new": conv.ai_mode}},
    )
    await db.flush()

    from app.websocket.manager import manager as ws_manager

    await ws_manager.broadcast_to_clinic(current_user.clinic_id, {
        "type": "conversation_updated",
        "conversation_id": str(conv.id),
        "ai_mode": conv.ai_mode,
    })

    return conv


@router.post("/{conversation_id}/resolve", response_model=ConversationDetailResponse)
async def resolve_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_conversation(db, conversation_id, current_user.clinic_id)
    conv.status = "resolved"
    await db.flush()

    from app.websocket.manager import manager as ws_manager

    await ws_manager.broadcast_to_clinic(current_user.clinic_id, {
        "type": "conversation_updated",
        "conversation_id": str(conv.id),
        "status": conv.status,
    })

    return conv


@router.post("/{conversation_id}/suggestions")
async def generate_suggestions(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-powered response suggestions for manual mode."""
    conv = await _get_conversation(db, conversation_id, current_user.clinic_id)

    if conv.ai_mode:
        from app.core.exceptions import BadRequestError

        raise BadRequestError("Suggestions are only available in manual mode")

    from app.ai.agents.consultation_service import ConsultationService
    from app.ai.agents.escalation import EscalationDetector
    from app.ai.chains.response_chain import ResponseChain
    from app.services.ai_response_service import AIResponseService

    # Build a minimal AIResponseService for suggestion generation
    service = AIResponseService(
        db=db,
        consultation_service=ConsultationService(
            response_chain=ResponseChain.__new__(ResponseChain),
            escalation_detector=EscalationDetector.__new__(EscalationDetector),
        ),
    )
    suggestions = await service.generate_suggestions(conversation_id)
    return {"suggestions": suggestions}


class FeedbackRequest(BaseModel):
    rating: str  # "up" or "down"
    note: str | None = None


@router.post("/{conversation_id}/messages/{message_id}/feedback")
async def submit_message_feedback(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    body: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback (thumbs up/down) for an AI message."""
    # Verify conversation belongs to clinic
    await _get_conversation(db, conversation_id, current_user.clinic_id)

    # Load message
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
        )
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise NotFoundError("Message not found")

    if message.sender_type != "ai":
        from app.core.exceptions import BadRequestError

        raise BadRequestError("Feedback is only allowed on AI messages")

    # Store feedback in ai_metadata
    metadata = message.ai_metadata or {}
    metadata["feedback"] = {
        "rating": body.rating,
        "note": body.note,
        "by": str(current_user.id),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    message.ai_metadata = metadata
    await db.flush()

    return {"status": "ok", "feedback": metadata["feedback"]}
