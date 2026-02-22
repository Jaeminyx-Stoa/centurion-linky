export interface ChartDraftContent {
  chief_complaint?: string;
  desired_procedures?: string[];
  medical_history?: string;
  allergies?: string;
  medications?: string;
  skin_type?: string;
  ai_recommendations?: string;
  notes?: string;
}

export interface ConsentFormContent {
  procedure_name: string;
  procedure_description?: string;
  risks?: string[];
  alternatives?: string;
  expected_results?: string;
  aftercare_instructions?: string;
  patient_acknowledgements?: string[];
}

export interface MedicalDocument {
  id: string;
  clinic_id: string;
  customer_id: string;
  customer_name: string | null;
  booking_id: string | null;
  conversation_id: string | null;
  document_type: "chart_draft" | "consent_form";
  title: string;
  content: ChartDraftContent | ConsentFormContent | null;
  language: string;
  status: "draft" | "reviewed" | "signed" | "archived";
  generated_by: "ai" | "staff";
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MedicalDocumentPaginated {
  items: MedicalDocument[];
  total: number;
  limit: number;
  offset: number;
}
