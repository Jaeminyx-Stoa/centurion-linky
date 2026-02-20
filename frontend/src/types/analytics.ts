export interface CRMDashboard {
  total_events: number;
  scheduled: number;
  sent: number;
  completed: number;
  cancelled: number;
  failed: number;
  total_surveys: number;
  avg_satisfaction: number | null;
  avg_nps: number | null;
}

export interface SatisfactionTrend {
  round: number;
  count: number;
  avg_score: number;
}

export interface NPSData {
  promoters: number;
  passives: number;
  detractors: number;
  nps: number;
  total: number;
}

export interface RevisitRate {
  yes: number;
  maybe: number;
  no: number;
  total: number;
  yes_rate: number;
}

export interface AIPersona {
  id: string;
  clinic_id: string;
  name: string;
  personality: string | null;
  system_prompt: string | null;
  avatar_url: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface MessengerAccount {
  id: string;
  clinic_id: string;
  messenger_type: string;
  account_name: string;
  display_name: string | null;
  webhook_url: string | null;
  target_countries: string[] | null;
  is_active: boolean;
  is_connected: boolean;
  last_synced_at: string | null;
  created_at: string;
}

export interface MessengerAccountCreate {
  messenger_type: string;
  account_name: string;
  display_name?: string;
  credentials: Record<string, string>;
  target_countries?: string[];
}

export interface MessengerAccountUpdate {
  account_name?: string;
  display_name?: string;
  credentials?: Record<string, string>;
  target_countries?: string[];
  is_active?: boolean;
}

export interface AnalyticsOverview {
  total_conversations: number;
  total_customers: number;
  total_bookings: number;
  total_revenue: number;
  ai_response_rate: number;
  avg_response_time: number;
}

export interface ConsultationPerformance {
  year: number;
  month: number;
  total_score: number;
  sales_mix_score: number;
  booking_conversion_score: number;
  payment_conversion_score: number;
  total_conversations: number;
  total_bookings: number;
  total_payments: number;
}

export interface SatisfactionScore {
  id: string;
  conversation_id: string;
  clinic_id: string;
  score: number;
  level: string;
  analysis: Record<string, unknown> | null;
  supervisor_override: number | null;
  created_at: string;
}

export interface CRMEventSummary {
  event_type: string;
  count: number;
}

