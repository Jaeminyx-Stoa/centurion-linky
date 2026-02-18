export interface Conversation {
  id: string;
  clinic_id: string;
  customer_id: string;
  messenger_account_id: string;
  status: string;
  ai_mode: boolean;
  satisfaction_score: number | null;
  satisfaction_level: string | null;
  last_message_at: string | null;
  last_message_preview: string | null;
  unread_count: number;
  created_at: string;
  // Joined
  customer_name: string | null;
  customer_country: string | null;
  customer_language: string | null;
  messenger_type: string | null;
}

export interface ConversationDetail {
  id: string;
  clinic_id: string;
  customer_id: string;
  messenger_account_id: string;
  status: string;
  ai_mode: boolean;
  assigned_to: string | null;
  satisfaction_score: number | null;
  satisfaction_level: string | null;
  last_message_at: string | null;
  last_message_preview: string | null;
  unread_count: number;
  summary: string | null;
  detected_intents: string[] | null;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: "customer" | "ai" | "staff";
  sender_id: string | null;
  content: string;
  content_type: string;
  original_language: string | null;
  translated_content: string | null;
  translated_language: string | null;
  messenger_type: string | null;
  ai_metadata: Record<string, unknown> | null;
  attachments: unknown[] | null;
  is_read: boolean;
  created_at: string;
}

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
