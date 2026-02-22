"""add consultation protocols

Revision ID: h0m8i9j0k1l2
Revises: g9l7h8i9j0k1
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "h0m8i9j0k1l2"
down_revision = "g9l7h8i9j0k1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consultation_protocols",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("clinic_id", sa.UUID(), sa.ForeignKey("clinics.id"), nullable=False, index=True),
        sa.Column("procedure_id", sa.UUID(), sa.ForeignKey("procedures.id"), nullable=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("checklist_items", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.add_column("bookings", sa.Column("protocol_state", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "protocol_state")
    op.drop_table("consultation_protocols")
