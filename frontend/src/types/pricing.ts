export { type ProcedurePricing, type ProcedureCategory } from "./procedure";

export interface ProcedurePricingCreate {
  clinic_procedure_id: string;
  regular_price: number;
  event_price?: number | null;
  discount_rate?: number | null;
  event_start_date?: string | null;
  event_end_date?: string | null;
  is_package?: boolean;
  package_details?: Record<string, unknown> | null;
  prices_by_currency?: Record<string, number>;
}

export interface ProcedurePricingUpdate {
  regular_price?: number;
  event_price?: number | null;
  discount_rate?: number | null;
  event_start_date?: string | null;
  event_end_date?: string | null;
  is_package?: boolean;
  package_details?: Record<string, unknown> | null;
  prices_by_currency?: Record<string, number>;
  is_active?: boolean;
}

export interface ProcedureCategoryCreate {
  name_ko: string;
  name_en?: string | null;
  slug: string;
  parent_id?: string | null;
  sort_order?: number;
}
