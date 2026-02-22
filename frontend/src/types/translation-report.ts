export interface TranslationReport {
  id: string;
  clinic_id: string;
  message_id: string | null;
  reported_by: string;
  source_language: string;
  target_language: string;
  original_text: string;
  translated_text: string;
  corrected_text: string | null;
  error_type: string;
  severity: string;
  medical_term_id: string | null;
  status: string;
  reviewer_id: string | null;
  reviewer_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface TranslationQAStats {
  total_reports: number;
  pending_count: number;
  resolved_count: number;
  critical_count: number;
  by_error_type: Record<string, number>;
  by_language_pair: { source: string; target: string; count: number }[];
  accuracy_score: number | null;
}

export interface TranslationReportPaginated {
  items: TranslationReport[];
  total: number;
  limit: number;
  offset: number;
}
