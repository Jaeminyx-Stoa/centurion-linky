export interface ABTestVariant {
  id: string;
  ab_test_id: string;
  name: string;
  config: Record<string, unknown>;
  weight: number;
  created_at: string;
}

export interface ABTest {
  id: string;
  clinic_id: string;
  name: string;
  description: string | null;
  test_type: string;
  status: string;
  is_active: boolean;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string | null;
  variants: ABTestVariant[];
}

export interface ABTestCreate {
  name: string;
  description?: string;
  test_type: string;
  variants: { name: string; config: Record<string, unknown>; weight?: number }[];
}

export interface ABTestStats {
  variant_id: string;
  variant_name: string;
  total_conversations: number;
  positive_outcomes: number;
  conversion_rate: number;
}

export interface SimulationPersona {
  name: string;
  profile: string;
  behavior: string;
  language: string;
  country: string;
}

export interface SimulationResult {
  id: string;
  session_id: string;
  clinic_id: string;
  booked: boolean;
  paid: boolean;
  escalated: boolean;
  abandoned: boolean;
  satisfaction_score: number | null;
  response_quality_score: number | null;
  exit_reason: string | null;
  strategies_used: string[] | null;
  notes: string | null;
  created_at: string;
}

export interface SimulationSession {
  id: string;
  clinic_id: string;
  persona_name: string;
  persona_config: Record<string, unknown>;
  max_rounds: number;
  actual_rounds: number;
  status: string;
  messages: unknown[] | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  result: SimulationResult | null;
}

export interface SimulationCreate {
  persona_name: string;
  max_rounds?: number;
}
