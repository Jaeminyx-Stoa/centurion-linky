export interface ChecklistItem {
  id: string;
  question_ko: string;
  question_en?: string;
  question_ja?: string;
  question_zh?: string;
  question_vi?: string;
  required: boolean;
  type: "boolean" | "text" | "choice";
  choices?: string[];
}

export interface ConsultationProtocol {
  id: string;
  clinic_id: string;
  procedure_id: string | null;
  name: string;
  checklist_items: ChecklistItem[] | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProtocolStateItem {
  id: string;
  answered: boolean;
  answer: string | null;
}

export interface ProtocolState {
  protocol_id: string;
  total_items: number;
  completed_items: number;
  is_complete: boolean;
  items: ProtocolStateItem[];
}
