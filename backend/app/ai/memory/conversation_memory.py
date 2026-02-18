import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message


class ConversationMemory:
    """PostgreSQL-based conversation memory for AI context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_memory(self, conversation_id: uuid.UUID) -> dict:
        """Load conversation memory: recent messages, customer context, summary."""
        # 1. Get conversation with customer
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation is None:
            return {
                "recent_messages": [],
                "customer_context": {},
                "summary": None,
                "total_message_count": 0,
            }

        # 2. Get total message count
        count_result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        total_count = count_result.scalar() or 0

        # 3. Get recent 20 messages (chronological order)
        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = list(reversed(msg_result.scalars().all()))

        recent_messages = [
            {
                "sender_type": m.sender_type,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ]

        # 4. Load customer context
        customer_context = await self._load_customer_context(conversation.customer_id)

        return {
            "recent_messages": recent_messages,
            "customer_context": customer_context,
            "summary": conversation.summary,
            "total_message_count": total_count,
        }

    async def _load_customer_context(self, customer_id: uuid.UUID) -> dict:
        """Load customer profile and related counts."""
        cust_result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        if customer is None:
            return {}

        # Count bookings
        booking_count_result = await self.db.execute(
            select(func.count(Booking.id)).where(
                Booking.customer_id == customer_id
            )
        )
        booking_count = booking_count_result.scalar() or 0

        return {
            "display_name": customer.display_name or customer.name,
            "language_code": customer.language_code,
            "country_code": customer.country_code,
            "timezone": customer.timezone,
            "booking_count": booking_count,
            "total_bookings": customer.total_bookings,
            "last_visit_at": customer.last_visit_at,
        }
