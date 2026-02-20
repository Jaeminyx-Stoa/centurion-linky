import { create } from "zustand";

import { api, buildPaginationParams } from "@/lib/api";
import type { Payment } from "@/types/payment";
import type { PaginatedResponse } from "@/types/api";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

interface PaymentState {
  payments: Payment[];
  isLoading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  total: number;

  fetchPayments: (token: string, bookingId?: string) => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
}

export const usePaymentStore = create<PaymentState>((set, get) => ({
  payments: [],
  isLoading: false,
  error: null,
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,

  fetchPayments: async (token, bookingId) => {
    set({ isLoading: true, error: null });
    try {
      const { page, pageSize } = get();
      const pagination = buildPaginationParams(page, pageSize);
      const bookingParam = bookingId ? `&booking_id=${bookingId}` : "";
      const data = await api.get<PaginatedResponse<Payment>>(
        `/api/v1/payments?${pagination}${bookingParam}`,
        { token },
      );
      set({ payments: data.items, total: data.total, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load payments" });
    }
  },

  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
}));
