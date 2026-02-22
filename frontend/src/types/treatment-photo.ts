export interface TreatmentPhoto {
  id: string;
  clinic_id: string;
  customer_id: string;
  booking_id: string | null;
  procedure_id: string | null;
  photo_type: "before" | "after" | "progress";
  photo_url: string;
  thumbnail_url: string | null;
  description: string | null;
  taken_at: string | null;
  days_after_procedure: number | null;
  is_consent_given: boolean;
  is_portfolio_approved: boolean;
  approved_by: string | null;
  pair_id: string | null;
  created_at: string;
}

export interface PhotoPair {
  pair_id: string;
  before: TreatmentPhoto | null;
  after: TreatmentPhoto | null;
}

export interface TreatmentPhotoPaginated {
  items: TreatmentPhoto[];
  total: number;
  limit: number;
  offset: number;
}
