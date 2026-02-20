import { create } from "zustand";

import { api } from "@/lib/api";
import type { Payment } from "@/types/payment";

interface PaymentState {
  payments: Payment[];
  isLoading: boolean;
  error: string | null;

  fetchPayments: (token: string, bookingId?: string) => Promise<void>;
}

export const usePaymentStore = create<PaymentState>((set) => ({
  payments: [],
  isLoading: false,
  error: null,

  fetchPayments: async (token, bookingId) => {
    set({ isLoading: true, error: null });
    try {
      const params = bookingId ? `?booking_id=${bookingId}` : "";
      const data = await api.get<Payment[]>(`/api/v1/payments${params}`, {
        token,
      });
      set({ payments: data, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load payments" });
    }
  },
}));
