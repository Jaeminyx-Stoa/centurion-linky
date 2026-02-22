"""add medical documents

Revision ID: j2o0k1l2m3n4
Revises: i1n9j0k1l2m3
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "j2o0k1l2m3n4"
down_revision = "i1n9j0k1l2m3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medical_documents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "clinic_id",
            sa.UUID(),
            sa.ForeignKey("clinics.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "customer_id",
            sa.UUID(),
            sa.ForeignKey("customers.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "booking_id",
            sa.UUID(),
            sa.ForeignKey("bookings.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            sa.ForeignKey("conversations.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", JSONB, nullable=True),
        sa.Column("language", sa.String(5), nullable=False, server_default="ko"),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="draft"
        ),
        sa.Column(
            "generated_by", sa.String(20), nullable=False, server_default="ai"
        ),
        sa.Column(
            "reviewed_by",
            sa.UUID(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.drop_table("medical_documents")
