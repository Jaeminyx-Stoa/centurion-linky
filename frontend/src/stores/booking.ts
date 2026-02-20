import { create } from "zustand";

import { api, buildPaginationParams } from "@/lib/api";
import type { Booking } from "@/types/booking";
import type { PaginatedResponse } from "@/types/api";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

interface BookingState {
  bookings: Booking[];
  isLoading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  total: number;

  fetchBookings: (token: string, status?: string) => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  updateBookingStatus: (
    token: string,
    id: string,
    data: Record<string, unknown>,
  ) => Promise<void>;
  cancelBooking: (
    token: string,
    id: string,
    reason?: string,
  ) => Promise<void>;
  completeBooking: (token: string, id: string) => Promise<void>;
}

export const useBookingStore = create<BookingState>((set, get) => ({
  bookings: [],
  isLoading: false,
  error: null,
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,

  fetchBookings: async (token, status) => {
    set({ isLoading: true, error: null });
    try {
      const { page, pageSize } = get();
      const pagination = buildPaginationParams(page, pageSize);
      const statusParam = status ? `&status=${status}` : "";
      const data = await api.get<PaginatedResponse<Booking>>(
        `/api/v1/bookings?${pagination}${statusParam}`,
        { token },
      );
      set({ bookings: data.items, total: data.total, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load bookings" });
    }
  },

  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),

  updateBookingStatus: async (token, id, data) => {
    await api.patch<Booking>(`/api/v1/bookings/${id}`, data, { token });
    await get().fetchBookings(token);
  },

  cancelBooking: async (token, id, reason) => {
    await api.post<Booking>(
      `/api/v1/bookings/${id}/cancel`,
      reason ? { cancellation_reason: reason } : {},
      { token },
    );
    await get().fetchBookings(token);
  },

  completeBooking: async (token, id) => {
    await api.post<Booking>(`/api/v1/bookings/${id}/complete`, {}, { token });
    await get().fetchBookings(token);
  },
}));
