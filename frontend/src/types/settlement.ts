export interface Settlement {
  id: string;
  clinic_id: string;
  period_year: number;
  period_month: number;
  total_payment_amount: number;
  commission_rate: number;
  commission_amount: number;
  vat_amount: number;
  total_settlement: number;
  total_payment_count: number;
  status: "pending" | "confirmed" | "paid";
  notes: string | null;
  confirmed_at: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string | null;
}
