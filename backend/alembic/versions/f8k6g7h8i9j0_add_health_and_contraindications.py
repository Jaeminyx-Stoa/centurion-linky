"""add health and contraindications

Revision ID: f8k6g7h8i9j0
Revises: e7j5f6g7h8i9
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "f8k6g7h8i9j0"
down_revision = "e7j5f6g7h8i9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("medical_conditions", JSONB, nullable=True))
    op.add_column("customers", sa.Column("allergies", JSONB, nullable=True))
    op.add_column("customers", sa.Column("medications", JSONB, nullable=True))
    op.add_column("procedures", sa.Column("contraindications", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("procedures", "contraindications")
    op.drop_column("customers", "medications")
    op.drop_column("customers", "allergies")
    op.drop_column("customers", "medical_conditions")
