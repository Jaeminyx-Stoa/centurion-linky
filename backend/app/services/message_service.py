import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.messenger.base import StandardMessage
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message


class MessageService:
    """Handles incoming messages from all messenger platforms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_incoming(self, msg: StandardMessage) -> Message:
        """Process an incoming message: upsert customer, upsert conversation, save message."""
        # 1. Customer upsert
        customer = await self._upsert_customer(msg)

        # 2. Conversation upsert
        conversation = await self._get_or_create_conversation(msg, customer)

        # 3. Save message
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            clinic_id=msg.clinic_id,
            sender_type="customer",
            sender_id=customer.id,
            content=msg.content,
            content_type=msg.content_type,
            messenger_type=msg.messenger_type,
            messenger_message_id=msg.messenger_message_id,
            original_language=customer.language_code,
            attachments=msg.attachments if msg.attachments else [],
        )
        self.db.add(message)

        # 4. Update conversation metadata
        conversation.last_message_at = datetime.now(timezone.utc)
        conversation.last_message_preview = msg.content[:200] if msg.content else ""
        conversation.unread_count = (conversation.unread_count or 0) + 1

        if conversation.status == "resolved":
            conversation.status = "active"

        await self.db.flush()

        return message

    async def _upsert_customer(self, msg: StandardMessage) -> Customer:
        """Find or create a customer by messenger identity."""
        result = await self.db.execute(
            select(Customer).where(
                Customer.clinic_id == msg.clinic_id,
                Customer.messenger_type == msg.messenger_type,
                Customer.messenger_user_id == msg.messenger_user_id,
            )
        )
        customer = result.scalar_one_or_none()

        if customer is None:
            customer = Customer(
                id=uuid.uuid4(),
                clinic_id=msg.clinic_id,
                messenger_type=msg.messenger_type,
                messenger_user_id=msg.messenger_user_id,
            )
            self.db.add(customer)
            await self.db.flush()

        return customer

    async def _get_or_create_conversation(
        self, msg: StandardMessage, customer: Customer
    ) -> Conversation:
        """Find active conversation or create a new one."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.customer_id == customer.id,
                Conversation.messenger_account_id == msg.account_id,
                Conversation.status.in_(["active", "waiting"]),
            )
        )
        conversation = result.scalar_one_or_none()

        if conversation is None:
            conversation = Conversation(
                id=uuid.uuid4(),
                clinic_id=msg.clinic_id,
                customer_id=customer.id,
                messenger_account_id=msg.account_id,
                status="active",
                ai_mode=True,
            )
            self.db.add(conversation)
            await self.db.flush()

        return conversation
