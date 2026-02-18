import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    MessageResponse,
    SendMessageRequest,
)

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


@router.get("", response_model=list[ConversationListResponse])
async def list_conversations(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Conversation).where(
        Conversation.clinic_id == current_user.clinic_id,
    ).order_by(Conversation.last_message_at.desc().nulls_last())

    if status:
        query = query.where(Conversation.status == status)

    result = await db.execute(query)
    conversations = result.scalars().all()

    items = []
    for conv in conversations:
        customer = await conv.awaitable_attrs.customer
        account = await conv.awaitable_attrs.messenger_account
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
    return items


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
    conv.ai_mode = not conv.ai_mode
    if not conv.ai_mode:
        conv.assigned_to = current_user.id
    else:
        conv.assigned_to = None
    await db.flush()
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
    return conv
