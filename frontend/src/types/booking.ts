export interface Booking {
  id: string;
  clinic_id: string;
  customer_id: string;
  conversation_id: string | null;
  clinic_procedure_id: string | null;
  booking_date: string;
  booking_time: string;
  status: string;
  total_amount: number | null;
  currency: string;
  deposit_amount: number | null;
  remaining_amount: number | null;
  notes: string | null;
  cancellation_reason: string | null;
  created_at: string;
  updated_at: string;
}

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export const BOOKING_STATUS_LABELS: Record<BookingStatus, string> = {
  pending: "대기",
  confirmed: "확정",
  completed: "완료",
  cancelled: "취소",
  no_show: "노쇼",
};

export const BOOKING_STATUS_COLORS: Record<BookingStatus, string> = {
  pending: "bg-yellow-50 text-yellow-700",
  confirmed: "bg-blue-50 text-blue-700",
  completed: "bg-green-50 text-green-700",
  cancelled: "bg-gray-100 text-gray-500",
  no_show: "bg-red-50 text-red-700",
};
