"""add followup rules

Revision ID: i1n9j0k1l2m3
Revises: h0m8i9j0k1l2
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "i1n9j0k1l2m3"
down_revision = "h0m8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "followup_rules",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "clinic_id",
            sa.UUID(),
            sa.ForeignKey("clinics.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "procedure_id",
            sa.UUID(),
            sa.ForeignKey("procedures.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("delay_days", sa.Integer(), nullable=False),
        sa.Column("delay_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message_template", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "side_effect_keywords",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "clinic_id",
            sa.UUID(),
            sa.ForeignKey("clinics.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("keywords", JSONB, nullable=False),
        sa.Column("severity", sa.String(10), nullable=False, server_default="normal"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("side_effect_keywords")
    op.drop_table("followup_rules")
