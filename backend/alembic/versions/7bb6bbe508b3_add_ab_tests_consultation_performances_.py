"""add ab_tests consultation_performances simulations tables

Revision ID: 7bb6bbe508b3
Revises: 1a4ddc383aa2
Create Date: 2026-02-18 23:30:58.108464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7bb6bbe508b3'
down_revision: Union[str, Sequence[str], None] = '1a4ddc383aa2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # A/B Tests
    op.create_table(
        'ab_tests',
        sa.Column('clinic_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('test_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), default='draft'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ab_tests_clinic_id', 'ab_tests', ['clinic_id'])

    op.create_table(
        'ab_test_variants',
        sa.Column('ab_test_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column('weight', sa.Integer(), default=50),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ab_test_id'], ['ab_tests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ab_test_results',
        sa.Column('ab_test_id', sa.Uuid(), nullable=False),
        sa.Column('variant_id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('outcome_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ab_test_id'], ['ab_tests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['ab_test_variants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ab_test_results_ab_test_id', 'ab_test_results', ['ab_test_id'])

    # Consultation Performance
    op.create_table(
        'consultation_performances',
        sa.Column('clinic_id', sa.Uuid(), nullable=False),
        sa.Column('period_year', sa.Integer(), nullable=False),
        sa.Column('period_month', sa.Integer(), nullable=False),
        sa.Column('total_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('sales_mix_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('booking_conversion_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('payment_conversion_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('booking_conversion_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('payment_conversion_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('total_consultations', sa.Integer(), default=0),
        sa.Column('total_bookings', sa.Integer(), default=0),
        sa.Column('total_payments', sa.Integer(), default=0),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clinic_id', 'period_year', 'period_month'),
    )
    op.create_index('ix_consultation_performances_clinic_id', 'consultation_performances', ['clinic_id'])

    # Simulation Sessions
    op.create_table(
        'simulation_sessions',
        sa.Column('clinic_id', sa.Uuid(), nullable=False),
        sa.Column('persona_name', sa.String(length=100), nullable=False),
        sa.Column('persona_config', postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column('max_rounds', sa.Integer(), default=20),
        sa.Column('actual_rounds', sa.Integer(), default=0),
        sa.Column('status', sa.String(length=20), default='pending'),
        sa.Column('messages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_sessions_clinic_id', 'simulation_sessions', ['clinic_id'])

    # Simulation Results
    op.create_table(
        'simulation_results',
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('clinic_id', sa.Uuid(), nullable=False),
        sa.Column('booked', sa.Boolean(), default=False),
        sa.Column('paid', sa.Boolean(), default=False),
        sa.Column('escalated', sa.Boolean(), default=False),
        sa.Column('abandoned', sa.Boolean(), default=False),
        sa.Column('satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('response_quality_score', sa.Integer(), nullable=True),
        sa.Column('exit_reason', sa.String(length=100), nullable=True),
        sa.Column('strategies_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['session_id'], ['simulation_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index('ix_simulation_results_clinic_id', 'simulation_results', ['clinic_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_simulation_results_clinic_id', table_name='simulation_results')
    op.drop_table('simulation_results')
    op.drop_index('ix_simulation_sessions_clinic_id', table_name='simulation_sessions')
    op.drop_table('simulation_sessions')
    op.drop_index('ix_consultation_performances_clinic_id', table_name='consultation_performances')
    op.drop_table('consultation_performances')
    op.drop_index('ix_ab_test_results_ab_test_id', table_name='ab_test_results')
    op.drop_table('ab_test_results')
    op.drop_table('ab_test_variants')
    op.drop_index('ix_ab_tests_clinic_id', table_name='ab_tests')
    op.drop_table('ab_tests')
