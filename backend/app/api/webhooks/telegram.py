import logging
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.messenger.telegram import TelegramAdapter
from app.models.messenger_account import MessengerAccount
from app.services.ai_response_background import broadcast_incoming_message
from app.services.message_service import MessageService
from app.tasks.ai_response import generate_ai_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/telegram", tags=["webhooks"])

adapter = TelegramAdapter()


@router.post("/{account_id}")
async def telegram_webhook(
    account_id: uuid.UUID,
    request: Request,
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
    processed = 0
    failed = 0
    for msg in messages:
        try:
            processing_result = await message_service.process_incoming(msg)

            # 5. Broadcast incoming message to staff dashboard
            await broadcast_incoming_message(
                processing_result.message, account.clinic_id
            )

            # 6. Queue AI auto-response via Celery
            if msg.content_type == "text" and msg.content:
                generate_ai_response.delay(
                    message_id=str(processing_result.message.id),
                    conversation_id=str(processing_result.conversation.id),
                    idempotency_key=f"telegram-{processing_result.message.id}",
                )
            processed += 1
        except Exception:
            failed += 1
            logger.exception(
                "Telegram webhook message processing failed: "
                "account_id=%s messenger_user=%s",
                account_id,
                msg.messenger_user_id,
            )

    logger.info(
        "Telegram webhook processed: account_id=%s processed=%d failed=%d",
        account_id,
        processed,
        failed,
    )
    return {"status": "ok"}
