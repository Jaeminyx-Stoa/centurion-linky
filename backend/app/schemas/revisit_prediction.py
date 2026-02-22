import uuid
from datetime import date

from pydantic import BaseModel


class ChurnRiskCustomer(BaseModel):
    customer_id: uuid.UUID
    customer_name: str | None
    country_code: str | None
    last_visit: date | None
    days_since_last_visit: int
    visit_count: int
    total_payments: float
    procedure_name: str | None  # last procedure
    expected_revisit_days: int | None  # based on procedure min_interval_days
    overdue_days: int  # how many days past expected revisit
    churn_risk_score: int  # 0-100 (100 = highest risk)
    risk_level: str  # low / medium / high / critical
    revisit_intention: str | None  # from satisfaction survey


class ChurnRiskResponse(BaseModel):
    total_at_risk: int
    critical_count: int
    high_count: int
    medium_count: int
    customers: list[ChurnRiskCustomer]


class RevisitSummary(BaseModel):
    total_customers: int
    due_this_week: int
    due_this_month: int
    overdue: int
    avg_churn_risk: float
