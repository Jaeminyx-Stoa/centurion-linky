"""Revisit prediction and churn risk scoring service.

Calculates churn risk score (0-100) for each customer based on:
- Days since last visit vs procedure's expected revisit interval
- Visit frequency pattern
- Satisfaction survey revisit intention
- Total payment history
"""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.clinic_procedure import ClinicProcedure
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.procedure import Procedure
from app.models.satisfaction_survey import SatisfactionSurvey


class RevisitPredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_churn_risk_customers(
        self,
        clinic_id: uuid.UUID,
        min_risk: int = 30,
        limit: int = 50,
    ) -> list[dict]:
        """Get customers sorted by churn risk score."""
        # Get all customers with completed bookings
        result = await self.db.execute(
            select(
                Customer.id,
                Customer.name,
                Customer.country_code,
                func.max(Booking.booking_date).label("last_visit"),
                func.count(func.distinct(Booking.booking_date)).label("visit_count"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_payments"),
            )
            .select_from(Customer)
            .join(Booking, Booking.customer_id == Customer.id)
            .outerjoin(Payment, Payment.customer_id == Customer.id)
            .where(
                Customer.clinic_id == clinic_id,
                Booking.clinic_id == clinic_id,
                Booking.status == "completed",
            )
            .group_by(Customer.id, Customer.name, Customer.country_code)
        )
        rows = result.all()

        customers = []
        today = date.today()

        for row in rows:
            last_visit = row.last_visit
            if not last_visit:
                continue

            days_since = (today - last_visit).days

            # Get last procedure's min_interval_days
            proc_result = await self.db.execute(
                select(Procedure.name_ko, Procedure.min_interval_days)
                .select_from(Booking)
                .join(ClinicProcedure, Booking.clinic_procedure_id == ClinicProcedure.id)
                .join(Procedure, ClinicProcedure.procedure_id == Procedure.id)
                .where(
                    Booking.customer_id == row.id,
                    Booking.clinic_id == clinic_id,
                    Booking.status == "completed",
                )
                .order_by(Booking.booking_date.desc())
                .limit(1)
            )
            proc_row = proc_result.one_or_none()
            procedure_name = proc_row.name_ko if proc_row else None
            expected_days = proc_row.min_interval_days if proc_row else None

            # Get revisit intention from latest survey
            survey_result = await self.db.execute(
                select(SatisfactionSurvey.revisit_intention)
                .where(
                    SatisfactionSurvey.customer_id == row.id,
                    SatisfactionSurvey.clinic_id == clinic_id,
                    SatisfactionSurvey.revisit_intention.isnot(None),
                )
                .order_by(SatisfactionSurvey.created_at.desc())
                .limit(1)
            )
            revisit_intention = survey_result.scalar_one_or_none()

            # Calculate churn risk score
            score = self._calculate_risk_score(
                days_since_last_visit=days_since,
                expected_revisit_days=expected_days,
                visit_count=row.visit_count,
                revisit_intention=revisit_intention,
                total_payments=float(row.total_payments),
            )

            overdue = 0
            if expected_days and days_since > expected_days:
                overdue = days_since - expected_days

            if score >= min_risk:
                customers.append({
                    "customer_id": row.id,
                    "customer_name": row.name,
                    "country_code": row.country_code,
                    "last_visit": last_visit,
                    "days_since_last_visit": days_since,
                    "visit_count": row.visit_count,
                    "total_payments": float(row.total_payments),
                    "procedure_name": procedure_name,
                    "expected_revisit_days": expected_days,
                    "overdue_days": overdue,
                    "churn_risk_score": score,
                    "risk_level": self._risk_level(score),
                    "revisit_intention": revisit_intention,
                })

        # Sort by risk score descending
        customers.sort(key=lambda x: x["churn_risk_score"], reverse=True)

        # Update cached scores on customer records
        for c in customers[:limit]:
            await self.db.execute(
                Customer.__table__.update()
                .where(Customer.id == c["customer_id"])
                .values(churn_risk_score=c["churn_risk_score"])
            )

        return customers[:limit]

    async def get_revisit_summary(self, clinic_id: uuid.UUID) -> dict:
        """Get summary of revisit predictions."""
        customers = await self.get_churn_risk_customers(clinic_id, min_risk=0, limit=1000)

        today = date.today()
        week_from_now = today + timedelta(days=7)
        month_from_now = today + timedelta(days=30)

        due_this_week = 0
        due_this_month = 0
        overdue = 0

        for c in customers:
            exp = c["expected_revisit_days"]
            if not exp:
                continue
            expected_date = c["last_visit"] + timedelta(days=exp)
            if expected_date < today:
                overdue += 1
            elif expected_date <= week_from_now:
                due_this_week += 1
            elif expected_date <= month_from_now:
                due_this_month += 1

        avg_risk = (
            sum(c["churn_risk_score"] for c in customers) / len(customers)
            if customers
            else 0
        )

        return {
            "total_customers": len(customers),
            "due_this_week": due_this_week,
            "due_this_month": due_this_month,
            "overdue": overdue,
            "avg_churn_risk": round(avg_risk, 1),
        }

    @staticmethod
    def _calculate_risk_score(
        *,
        days_since_last_visit: int,
        expected_revisit_days: int | None,
        visit_count: int,
        revisit_intention: str | None,
        total_payments: float,
    ) -> int:
        """Calculate churn risk score (0-100).

        Factors:
        - Overdue ratio (40 points): How far past expected revisit
        - Visit frequency (20 points): Single visit = higher risk
        - Revisit intention (25 points): From satisfaction survey
        - Recency (15 points): Base time since last visit
        """
        score = 0

        # 1. Overdue ratio (40 points)
        if expected_revisit_days and expected_revisit_days > 0:
            overdue_ratio = days_since_last_visit / expected_revisit_days
            if overdue_ratio > 2.0:
                score += 40
            elif overdue_ratio > 1.5:
                score += 30
            elif overdue_ratio > 1.0:
                score += 20
            elif overdue_ratio > 0.8:
                score += 10
        else:
            # No interval data — use default 90-day cycle
            if days_since_last_visit > 180:
                score += 40
            elif days_since_last_visit > 120:
                score += 30
            elif days_since_last_visit > 90:
                score += 20
            elif days_since_last_visit > 60:
                score += 10

        # 2. Visit frequency (20 points)
        if visit_count == 1:
            score += 20  # Single-visit customers are highest risk
        elif visit_count == 2:
            score += 12
        elif visit_count <= 4:
            score += 5
        # 5+ visits = loyal, no additional risk

        # 3. Revisit intention (25 points)
        if revisit_intention == "no":
            score += 25
        elif revisit_intention == "maybe":
            score += 12
        elif revisit_intention == "yes":
            score += 0
        else:
            score += 8  # Unknown = some risk

        # 4. Recency (15 points)
        if days_since_last_visit > 365:
            score += 15
        elif days_since_last_visit > 180:
            score += 10
        elif days_since_last_visit > 90:
            score += 5

        return min(score, 100)

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 75:
            return "critical"
        if score >= 50:
            return "high"
        if score >= 30:
            return "medium"
        return "low"
