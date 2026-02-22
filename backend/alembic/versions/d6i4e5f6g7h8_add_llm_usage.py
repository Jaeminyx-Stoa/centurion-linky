"""Add llm_usages table.

Revision ID: d6i4e5f6g7h8
Revises: c5h3d4e6f7g8
Create Date: 2026-02-20 00:00:04.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d6i4e5f6g7h8"
down_revision = "c5h3d4e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_usages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
    )
    op.create_index("ix_llm_usages_clinic_id", "llm_usages", ["clinic_id"])
    op.create_index("ix_llm_usages_created_at", "llm_usages", ["created_at"])
    op.create_index("ix_llm_usages_operation", "llm_usages", ["operation"])


def downgrade() -> None:
    op.drop_index("ix_llm_usages_operation")
    op.drop_index("ix_llm_usages_created_at")
    op.drop_index("ix_llm_usages_clinic_id")
    op.drop_table("llm_usages")
