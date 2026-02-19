export interface ResponseLibrary {
  id: string;
  clinic_id: string;
  category: string;
  subcategory: string | null;
  question: string;
  answer: string;
  language_code: string;
  tags: string[] | null;
  is_active: boolean;
  created_at: string;
}

export interface ResponseLibraryCreate {
  category: string;
  question: string;
  answer: string;
  subcategory?: string;
  language_code?: string;
  tags?: string[];
}

export interface ResponseLibraryUpdate {
  category?: string;
  question?: string;
  answer?: string;
  subcategory?: string;
  language_code?: string;
  tags?: string[];
  is_active?: boolean;
}

export interface MedicalTerm {
  id: string;
  clinic_id: string | null;
  term_ko: string;
  translations: Record<string, string>;
  category: string;
  description: string | null;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface MedicalTermCreate {
  term_ko: string;
  translations: Record<string, string>;
  category: string;
  description?: string;
}

export interface MedicalTermUpdate {
  term_ko?: string;
  translations?: Record<string, string>;
  category?: string;
  description?: string;
  is_verified?: boolean;
  is_active?: boolean;
}
