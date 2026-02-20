import { create } from "zustand";

import { api } from "@/lib/api";
import type { Booking } from "@/types/booking";

interface BookingState {
  bookings: Booking[];
  isLoading: boolean;
  error: string | null;

  fetchBookings: (token: string, status?: string) => Promise<void>;
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

  fetchBookings: async (token, status) => {
    set({ isLoading: true, error: null });
    try {
      const params = status ? `?status=${status}` : "";
      const data = await api.get<Booking[]>(`/api/v1/bookings${params}`, {
        token,
      });
      set({ bookings: data, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load bookings" });
    }
  },

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
