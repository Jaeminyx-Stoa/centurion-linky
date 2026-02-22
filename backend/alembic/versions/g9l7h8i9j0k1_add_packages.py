"""add packages

Revision ID: g9l7h8i9j0k1
Revises: f8k6g7h8i9j0
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "g9l7h8i9j0k1"
down_revision = "f8k6g7h8i9j0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "procedure_packages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("clinic_id", sa.UUID(), sa.ForeignKey("clinics.id"), nullable=False, index=True),
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=True),
        sa.Column("name_ja", sa.String(200), nullable=True),
        sa.Column("name_zh", sa.String(200), nullable=True),
        sa.Column("name_vi", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("items", JSONB, nullable=True),
        sa.Column("total_sessions", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("package_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "package_enrollments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("clinic_id", sa.UUID(), sa.ForeignKey("clinics.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("package_id", sa.UUID(), sa.ForeignKey("procedure_packages.id"), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("purchased_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sessions_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_session_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "package_sessions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("enrollment_id", sa.UUID(), sa.ForeignKey("package_enrollments.id"), nullable=False, index=True),
        sa.Column("session_number", sa.Integer(), nullable=False),
        sa.Column("clinic_procedure_id", sa.UUID(), sa.ForeignKey("clinic_procedures.id"), nullable=True),
        sa.Column("booking_id", sa.UUID(), sa.ForeignKey("bookings.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("package_sessions")
    op.drop_table("package_enrollments")
    op.drop_table("procedure_packages")
