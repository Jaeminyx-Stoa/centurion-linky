export interface ChurnRiskCustomer {
  customer_id: string;
  customer_name: string | null;
  country_code: string | null;
  last_visit: string | null;
  days_since_last_visit: number;
  visit_count: number;
  total_payments: number;
  procedure_name: string | null;
  expected_revisit_days: number | null;
  overdue_days: number;
  churn_risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  revisit_intention: string | null;
}

export interface ChurnRiskResponse {
  total_at_risk: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  customers: ChurnRiskCustomer[];
}

export interface RevisitSummary {
  total_customers: number;
  due_this_week: number;
  due_this_month: number;
  overdue: number;
  avg_churn_risk: number;
}
