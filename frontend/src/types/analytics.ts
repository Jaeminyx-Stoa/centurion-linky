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
  platform: string;
  account_name: string | null;
  account_id: string | null;
  is_active: boolean;
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
}
