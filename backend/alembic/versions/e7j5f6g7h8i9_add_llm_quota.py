"""Add LLM quota fields to clinics table.

Revision ID: e7j5f6g7h8i9
Revises: d6i4e5f6g7h8
Create Date: 2026-02-20 00:00:05.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e7j5f6g7h8i9"
down_revision = "d6i4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("llm_monthly_quota_usd", sa.Float(), nullable=True),
    )
    op.add_column(
        "clinics",
        sa.Column(
            "llm_quota_alert_sent",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("clinics", "llm_quota_alert_sent")
    op.drop_column("clinics", "llm_monthly_quota_usd")
