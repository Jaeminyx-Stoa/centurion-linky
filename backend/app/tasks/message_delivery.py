"""Celery task for retrying failed messenger message deliveries."""

import asyncio
import logging
import uuid

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.message_delivery.retry_message_delivery",
    max_retries=5,
    default_retry_delay=30,
)
def retry_message_delivery(
    self,
    message_id: str,
    account_id: str,
    recipient_id: str,
    text: str,
    messenger_type: str,
):
    """Retry delivering a message via messenger adapter.

    Uses exponential backoff: 30s, 60s, 120s, 240s, 480s.
    On final failure, sends a WebSocket notification.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    try:
        result = loop.run_until_complete(
            _deliver(message_id, account_id, recipient_id, text, messenger_type)
        )
        return result
    except Exception as exc:
        retry_num = self.request.retries
        logger.warning(
            "Message delivery attempt %d/%d failed for message %s: %s",
            retry_num + 1,
            self.max_retries,
            message_id,
            str(exc),
        )
        if retry_num < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (2 ** retry_num))
        else:
            # Final failure — notify via WebSocket
            logger.error(
                "Message delivery permanently failed for message %s after %d retries",
                message_id,
                self.max_retries,
            )
            loop.run_until_complete(
                _notify_delivery_failed(message_id, messenger_type)
            )
            raise


async def _deliver(
    message_id: str,
    account_id: str,
    recipient_id: str,
    text: str,
    messenger_type: str,
) -> dict:
    """Attempt to deliver the message and update the DB record."""
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.messenger.factory import MessengerAdapterFactory
    from app.models.message import Message
    from app.models.messenger_account import MessengerAccount

    async with async_session_factory() as db:
        # Load messenger account
        result = await db.execute(
            select(MessengerAccount).where(
                MessengerAccount.id == uuid.UUID(account_id)
            )
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise ValueError(f"MessengerAccount {account_id} not found")

        # Send via adapter
        adapter = MessengerAdapterFactory.get_adapter(messenger_type)
        messenger_msg_id = await adapter.send_message(account, recipient_id, text)

        # Update message record
        msg_result = await db.execute(
            select(Message).where(Message.id == uuid.UUID(message_id))
        )
        message = msg_result.scalar_one_or_none()
        if message:
            message.messenger_message_id = messenger_msg_id

        await db.commit()

    return {"message_id": message_id, "messenger_message_id": messenger_msg_id}


async def _notify_delivery_failed(message_id: str, messenger_type: str):
    """Send a WebSocket notification about permanent delivery failure."""
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.message import Message
    from app.websocket.manager import manager

    async with async_session_factory() as db:
        result = await db.execute(
            select(Message).where(Message.id == uuid.UUID(message_id))
        )
        message = result.scalar_one_or_none()
        if message:
            await manager.broadcast_to_clinic(
                message.clinic_id,
                {
                    "type": "delivery_failed",
                    "message_id": message_id,
                    "conversation_id": str(message.conversation_id),
                    "messenger_type": messenger_type,
                },
            )
