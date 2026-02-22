"""Celery tasks for CRM event execution (periodic + on-demand)."""

import asyncio
import logging
import uuid

from celery import Task

from app.tasks import celery_app

logger = logging.getLogger(__name__)


class CRMExecutionTask(Task):
    """Base task class for CRM execution."""

    _loop = None

    @property
    def loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop


@celery_app.task(
    base=CRMExecutionTask,
    bind=True,
    name="app.tasks.crm_execution.execute_due_events",
    max_retries=1,
    soft_time_limit=300,
    time_limit=360,
)
def execute_due_events(self: CRMExecutionTask) -> dict:
    """Periodic task: find and execute all due CRM events.

    Runs every 5 minutes via Celery Beat.
    """
    logger.info("CRM execution sweep started")
    try:
        result = self.loop.run_until_complete(_execute_due_events())
        logger.info(
            "CRM execution sweep finished: sent=%d failed=%d",
            result["sent"],
            result["failed"],
        )
        return result
    except Exception:
        logger.exception("CRM execution sweep failed")
        raise self.retry(countdown=60)


@celery_app.task(
    base=CRMExecutionTask,
    bind=True,
    name="app.tasks.crm_execution.schedule_crm_for_payment",
    max_retries=3,
    default_retry_delay=10,
)
def schedule_crm_for_payment(self: CRMExecutionTask, payment_id: str) -> dict:
    """Schedule CRM timeline when a payment is completed."""
    logger.info("Scheduling CRM timeline for payment=%s", payment_id)
    try:
        result = self.loop.run_until_complete(
            _schedule_crm_for_payment(uuid.UUID(payment_id))
        )
        return result
    except Exception as exc:
        logger.exception("CRM schedule failed for payment=%s", payment_id)
        raise self.retry(exc=exc)


async def _execute_due_events() -> dict:
    """Async implementation: query due events and send messages."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.core.database import async_session_factory
    from app.messenger.factory import MessengerAdapterFactory
    from app.models.conversation import Conversation
    from app.models.crm_event import CRMEvent
    from app.services.crm_service import CRMService

    sent = 0
    failed = 0

    async with async_session_factory() as db:
        try:
            service = CRMService(db)
            due_events = await service.get_due_events()

            if not due_events:
                await db.commit()
                return {"sent": 0, "failed": 0}

            for event in due_events:
                try:
                    # Find the customer's most recent conversation to get messenger info
                    conv_result = await db.execute(
                        select(Conversation)
                        .options(
                            selectinload(Conversation.customer),
                            selectinload(Conversation.messenger_account),
                        )
                        .where(
                            Conversation.customer_id == event.customer_id,
                            Conversation.clinic_id == event.clinic_id,
                        )
                        .order_by(Conversation.last_message_at.desc().nulls_last())
                        .limit(1)
                    )
                    conversation = conv_result.scalar_one_or_none()

                    if conversation is None:
                        logger.warning(
                            "No conversation found for CRM event %s (customer=%s)",
                            event.id,
                            event.customer_id,
                        )
                        await service.mark_failed(
                            event.id, "No conversation found for customer"
                        )
                        failed += 1
                        continue

                    customer = conversation.customer
                    account = conversation.messenger_account

                    # Build message content
                    message_text = event.message_content or _build_default_message(
                        event.event_type, customer.name or customer.display_name
                    )

                    # Send via messenger adapter
                    adapter = MessengerAdapterFactory.get_adapter(
                        account.messenger_type
                    )
                    await adapter.send_message(
                        account=account,
                        recipient_id=customer.messenger_user_id,
                        text=message_text,
                    )

                    await service.mark_sent(event.id)
                    sent += 1
                    logger.info(
                        "CRM event %s (%s) sent to customer %s",
                        event.id,
                        event.event_type,
                        event.customer_id,
                    )

                    # Broadcast CRM event sent via WebSocket
                    from app.websocket.manager import manager as ws_manager

                    await ws_manager.broadcast_to_clinic(event.clinic_id, {
                        "type": "crm_event_sent",
                        "event_id": str(event.id),
                        "event_type": event.event_type,
                        "customer_id": str(event.customer_id),
                    })

                except Exception as e:
                    logger.exception(
                        "Failed to execute CRM event %s: %s", event.id, e
                    )
                    try:
                        await service.mark_failed(event.id, str(e))
                    except Exception:
                        logger.exception(
                            "Failed to mark CRM event %s as failed", event.id
                        )
                    failed += 1

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return {"sent": sent, "failed": failed}


async def _schedule_crm_for_payment(payment_id: uuid.UUID) -> dict:
    """Async implementation: schedule CRM timeline for a payment."""
    from app.core.database import async_session_factory
    from app.services.crm_service import CRMService

    async with async_session_factory() as db:
        try:
            service = CRMService(db)
            events = await service.schedule_crm_timeline(payment_id)
            await db.commit()
            return {
                "status": "scheduled",
                "payment_id": str(payment_id),
                "events_count": len(events),
            }
        except Exception:
            await db.rollback()
            raise


def _build_default_message(event_type: str, customer_name: str | None) -> str:
    """Build a default message for a CRM event type."""
    name = customer_name or "Customer"
    messages = {
        "receipt": f"Hi {name}, thank you for your visit! Your payment has been confirmed.",
        "review_request": f"Hi {name}, we hope you're feeling great! Could you leave us a review about your experience?",
        "aftercare": f"Hi {name}, this is a friendly reminder about your aftercare instructions. Please follow the guidelines provided by your doctor.",
        "survey_1": f"Hi {name}, how are you feeling after your procedure? We'd love to hear about your experience.",
        "survey_2": f"Hi {name}, it's been a week since your procedure. How is your recovery going?",
        "survey_3": f"Hi {name}, it's been two weeks since your procedure. We'd appreciate your feedback on the results.",
        "revisit_reminder": f"Hi {name}, it's been a while since your last visit. Would you like to schedule a follow-up?",
    }
    return messages.get(event_type, f"Hi {name}, thank you for choosing our clinic!")
