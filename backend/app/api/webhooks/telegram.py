import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.messenger.telegram import TelegramAdapter
from app.models.messenger_account import MessengerAccount
from app.services.ai_response_background import (
    broadcast_incoming_message,
    process_ai_response_background,
)
from app.services.message_service import MessageService

router = APIRouter(prefix="/webhooks/telegram", tags=["webhooks"])

adapter = TelegramAdapter()


@router.post("/{account_id}")
async def telegram_webhook(
    account_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # 1. Find account
    result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise NotFoundError("Messenger account not found")

    if not account.is_active:
        raise PermissionDeniedError("Messenger account is inactive")

    # 2. Verify webhook signature
    body = await request.body()
    headers = dict(request.headers)
    is_valid = await adapter.verify_webhook(body, headers, secret=account.webhook_secret)
    if not is_valid:
        raise PermissionDeniedError("Invalid webhook signature")

    # 3. Parse webhook
    payload = await request.json()
    messages = await adapter.parse_webhook(account, payload)

    # 4. Process each message
    message_service = MessageService(db)
    for msg in messages:
        processing_result = await message_service.process_incoming(msg)

        # 5. Broadcast incoming message to staff dashboard
        await broadcast_incoming_message(
            processing_result.message, account.clinic_id
        )

        # 6. Trigger AI auto-response for text messages
        if msg.content_type == "text" and msg.content:
            background_tasks.add_task(
                process_ai_response_background,
                message_id=processing_result.message.id,
                conversation_id=processing_result.conversation.id,
                session_factory=async_session_factory,
            )

    return {"status": "ok"}
