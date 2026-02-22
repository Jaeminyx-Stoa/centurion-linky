export interface HealthItem {
  name: string;
  severity?: string;
  notes?: string;
}

export interface HealthData {
  items: HealthItem[];
}

export interface Customer {
  id: string;
  clinic_id: string;
  messenger_type: string;
  messenger_user_id: string;
  name: string | null;
  display_name: string | null;
  profile_image: string | null;
  country_code: string | null;
  language_code: string | null;
  timezone: string | null;
  phone: string | null;
  email: string | null;
  tags: string[] | null;
  notes: string | null;
  medical_conditions: HealthData | null;
  allergies: HealthData | null;
  medications: HealthData | null;
  total_bookings: number;
  last_visit_at: string | null;
  created_at: string;
}

export interface CustomerUpdate {
  name?: string;
  phone?: string;
  email?: string;
  tags?: string[];
  notes?: string;
  medical_conditions?: HealthData;
  allergies?: HealthData;
  medications?: HealthData;
}

export interface ContraindicationWarning {
  severity: "critical" | "warning" | "info";
  category: string;
  procedure_name: string;
  detail: string;
  matched_customer_item: string;
  matched_procedure_item: string;
}

export interface ContraindicationCheckResponse {
  has_warnings: boolean;
  critical_count: number;
  warning_count: number;
  info_count: number;
  warnings: ContraindicationWarning[];
}
