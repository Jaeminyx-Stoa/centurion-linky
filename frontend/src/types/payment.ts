export interface Payment {
  id: string;
  clinic_id: string;
  booking_id: string | null;
  customer_id: string;
  payment_type: string;
  amount: number;
  currency: string;
  pg_provider: string | null;
  pg_payment_id: string | null;
  payment_method: string | null;
  payment_link: string | null;
  qr_code_url: string | null;
  link_expires_at: string | null;
  status: string;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}

export type PaymentStatus =
  | "pending"
  | "completed"
  | "failed"
  | "refunded"
  | "expired";

export const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  pending: "대기",
  completed: "완료",
  failed: "실패",
  refunded: "환불",
  expired: "만료",
};

export const PAYMENT_STATUS_COLORS: Record<PaymentStatus, string> = {
  pending: "bg-yellow-50 text-yellow-700",
  completed: "bg-green-50 text-green-700",
  failed: "bg-red-50 text-red-700",
  refunded: "bg-purple-50 text-purple-700",
  expired: "bg-gray-100 text-gray-500",
};
