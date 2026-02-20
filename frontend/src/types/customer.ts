export interface Customer {
  id: string;
  clinic_id: string;
  messenger_type: string;
  messenger_user_id: string;
  name: string | null;
  display_name: string | null;
  profile_image: string | null;
  country_code: string | null;
  language_code: string | null;
  timezone: string | null;
  phone: string | null;
  email: string | null;
  tags: string[] | null;
  notes: string | null;
  total_bookings: number;
  last_visit_at: string | null;
  created_at: string;
}

export interface CustomerUpdate {
  name?: string;
  phone?: string;
  email?: string;
  tags?: string[];
  notes?: string;
}
