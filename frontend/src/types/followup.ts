export interface FollowupRule {
  id: string;
  clinic_id: string;
  procedure_id: string | null;
  procedure_name: string | null;
  event_type: string;
  delay_days: number;
  delay_hours: number;
  message_template: Record<string, string> | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FollowupRuleCreate {
  procedure_id?: string | null;
  event_type: string;
  delay_days: number;
  delay_hours?: number;
  message_template?: Record<string, string> | null;
  sort_order?: number;
  is_active?: boolean;
}

export interface SideEffectKeyword {
  id: string;
  clinic_id: string;
  language: string;
  keywords: string[];
  severity: string;
  created_at: string;
  updated_at: string;
}

export interface SideEffectKeywordCreate {
  language: string;
  keywords: string[];
  severity: string;
}

export interface SideEffectAlert {
  customer_id: string;
  customer_name: string | null;
  conversation_id: string;
  matched_keywords: string[];
  severity: string;
  message_preview: string;
  detected_at: string;
}
