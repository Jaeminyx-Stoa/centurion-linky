"""add settlements table

Revision ID: 1a4ddc383aa2
Revises: 863ca1052999
Create Date: 2026-02-18 23:14:25.095617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a4ddc383aa2'
down_revision: Union[str, Sequence[str], None] = '863ca1052999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'settlements',
        sa.Column('clinic_id', sa.Uuid(), nullable=False),
        sa.Column('period_year', sa.Integer(), nullable=False),
        sa.Column('period_month', sa.Integer(), nullable=False),
        sa.Column('total_payment_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('commission_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('commission_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('vat_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_settlement', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_payment_count', sa.Integer(), default=0),
        sa.Column('status', sa.String(length=20), default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clinic_id', 'period_year', 'period_month'),
    )
    op.create_index('ix_settlements_clinic_id', 'settlements', ['clinic_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_settlements_clinic_id', table_name='settlements')
    op.drop_table('settlements')
