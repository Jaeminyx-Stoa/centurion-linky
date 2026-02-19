export interface ProcedureCategory {
  id: string;
  name_ko: string;
  name_en: string | null;
  name_ja: string | null;
  name_zh: string | null;
  slug: string;
  parent_id: string | null;
  sort_order: number;
}

export interface ProcedureCategoryTree extends ProcedureCategory {
  children: ProcedureCategoryTree[];
}

export interface Procedure {
  id: string;
  category_id: string | null;
  name_ko: string;
  name_en: string | null;
  name_ja: string | null;
  name_zh: string | null;
  name_vi: string | null;
  slug: string;
  description_ko: string | null;
  description_en: string | null;
  effects_ko: string | null;
  duration_minutes: number | null;
  effect_duration: string | null;
  downtime_days: number | null;
  min_interval_days: number | null;
  pain_level: number | null;
  anesthesia_options: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface ClinicProcedure {
  id: string;
  clinic_id: string;
  procedure_id: string;
  custom_name_ko: string | null;
  custom_description_ko: string | null;
  custom_effects_ko: string | null;
  custom_duration_minutes: number | null;
  custom_downtime_days: number | null;
  custom_precautions_before: string | null;
  custom_precautions_after: string | null;
  is_active: boolean;
  sales_performance_score: number | null;
  created_at: string;
  updated_at: string | null;
  // Joined
  procedure: Procedure | null;
}

export interface ProcedurePricing {
  id: string;
  clinic_procedure_id: string;
  clinic_id: string;
  regular_price: number;
  event_price: number | null;
  discount_rate: number | null;
  event_start_date: string | null;
  event_end_date: string | null;
  is_package: boolean;
  package_details: Record<string, unknown> | null;
  prices_by_currency: Record<string, number>;
  discount_warning: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}
