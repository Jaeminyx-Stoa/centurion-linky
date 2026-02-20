"""Add missing foreign key indexes for query performance.

Revision ID: a3f1b2c4d5e6
Revises: 487eda490e39
Create Date: 2026-02-20 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f1b2c4d5e6"
down_revision = "487eda490e39"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # conversations — high-traffic table, all FKs need indexes
    op.create_index("ix_conversations_clinic_id", "conversations", ["clinic_id"])
    op.create_index("ix_conversations_customer_id", "conversations", ["customer_id"])
    op.create_index("ix_conversations_messenger_account_id", "conversations", ["messenger_account_id"])

    # messages — very high-traffic, fetched per conversation
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_clinic_id", "messages", ["clinic_id"])

    # customers — filtered by clinic
    op.create_index("ix_customers_clinic_id", "customers", ["clinic_id"])

    # messenger_accounts — filtered by clinic
    op.create_index("ix_messenger_accounts_clinic_id", "messenger_accounts", ["clinic_id"])

    # response_library — filtered by clinic
    op.create_index("ix_response_library_clinic_id", "response_library", ["clinic_id"])

    # ai_personas — filtered by clinic
    op.create_index("ix_ai_personas_clinic_id", "ai_personas", ["clinic_id"])

    # crm_events — customer_id used in filters
    op.create_index("ix_crm_events_customer_id", "crm_events", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_crm_events_customer_id", "crm_events")
    op.drop_index("ix_ai_personas_clinic_id", "ai_personas")
    op.drop_index("ix_response_library_clinic_id", "response_library")
    op.drop_index("ix_messenger_accounts_clinic_id", "messenger_accounts")
    op.drop_index("ix_customers_clinic_id", "customers")
    op.drop_index("ix_messages_clinic_id", "messages")
    op.drop_index("ix_messages_conversation_id", "messages")
    op.drop_index("ix_conversations_messenger_account_id", "conversations")
    op.drop_index("ix_conversations_customer_id", "conversations")
    op.drop_index("ix_conversations_clinic_id", "conversations")
