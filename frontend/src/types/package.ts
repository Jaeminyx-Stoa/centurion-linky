export interface PackageItem {
  clinic_procedure_id: string;
  sessions: number;
  interval_days: number;
}

export interface ProcedurePackage {
  id: string;
  clinic_id: string;
  name_ko: string;
  name_en: string | null;
  name_ja: string | null;
  name_zh: string | null;
  name_vi: string | null;
  description: string | null;
  items: PackageItem[] | null;
  total_sessions: number;
  package_price: number | null;
  discount_rate: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PackageSession {
  id: string;
  enrollment_id: string;
  session_number: number;
  clinic_procedure_id: string | null;
  booking_id: string | null;
  status: string;
  scheduled_date: string | null;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface PackageEnrollment {
  id: string;
  clinic_id: string;
  customer_id: string;
  package_id: string;
  status: string;
  purchased_at: string | null;
  sessions_completed: number;
  next_session_date: string | null;
  notes: string | null;
  sessions: PackageSession[];
  created_at: string;
}
