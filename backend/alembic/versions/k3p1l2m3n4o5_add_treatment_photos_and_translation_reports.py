"""add treatment_photos and translation_reports

Revision ID: k3p1l2m3n4o5
Revises: j2o0k1l2m3n4
Create Date: 2026-02-22 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "k3p1l2m3n4o5"
down_revision = "j2o0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # treatment_photos table
    op.create_table(
        "treatment_photos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("booking_id", sa.Uuid(), sa.ForeignKey("bookings.id"), nullable=True),
        sa.Column("procedure_id", sa.Uuid(), sa.ForeignKey("procedures.id"), nullable=True),
        sa.Column("photo_type", sa.String(20), nullable=False),  # before / after / progress
        sa.Column("photo_url", sa.String(500), nullable=False),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_after_procedure", sa.Integer(), nullable=True),
        sa.Column("is_consent_given", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_portfolio_approved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("pair_id", sa.Uuid(), nullable=True),  # links before/after pairs
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_treatment_photos_clinic_id", "treatment_photos", ["clinic_id"])
    op.create_index("ix_treatment_photos_customer_id", "treatment_photos", ["customer_id"])
    op.create_index("ix_treatment_photos_booking_id", "treatment_photos", ["booking_id"])
    op.create_index("ix_treatment_photos_pair_id", "treatment_photos", ["pair_id"])

    # translation_reports table
    op.create_table(
        "translation_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("reported_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_language", sa.String(10), nullable=False),
        sa.Column("target_language", sa.String(10), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("corrected_text", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(30), nullable=False),  # wrong_term / wrong_meaning / awkward / omission / other
        sa.Column("severity", sa.String(10), nullable=False),  # critical / minor
        sa.Column("medical_term_id", sa.Uuid(), sa.ForeignKey("medical_terms.id"), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),  # pending / reviewed / resolved / dismissed
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_translation_reports_clinic_id", "translation_reports", ["clinic_id"])
    op.create_index("ix_translation_reports_status", "translation_reports", ["status"])

    # Add churn/revisit columns to customers
    op.add_column("customers", sa.Column("churn_risk_score", sa.Integer(), nullable=True))
    op.add_column("customers", sa.Column("predicted_next_visit", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "predicted_next_visit")
    op.drop_column("customers", "churn_risk_score")
    op.drop_table("translation_reports")
    op.drop_table("treatment_photos")
