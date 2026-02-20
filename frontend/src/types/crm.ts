export interface CRMEvent {
  id: string;
  clinic_id: string;
  customer_id: string;
  payment_id: string | null;
  booking_id: string | null;
  event_type: string;
  scheduled_at: string;
  executed_at: string | null;
  status: string;
  message_content: string | null;
  response: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SatisfactionSurvey {
  id: string;
  clinic_id: string;
  customer_id: string;
  booking_id: string | null;
  conversation_id: string | null;
  survey_round: number;
  overall_score: number;
  service_score: number | null;
  result_score: number | null;
  communication_score: number | null;
  nps_score: number | null;
  would_revisit: string | null;
  feedback_text: string | null;
  created_at: string;
}

export interface SurveySummary {
  total_surveys: number;
  avg_overall: number | null;
  avg_service: number | null;
  avg_result: number | null;
  avg_communication: number | null;
  avg_nps: number | null;
}
