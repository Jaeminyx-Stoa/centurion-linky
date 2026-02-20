import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useBookingStore } from "@/stores/booking";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPatch = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => vi.fn(),
  },
}));

const FAKE_TOKEN = "test-token";

const FAKE_BOOKING = {
  id: "booking-1",
  clinic_id: "clinic-1",
  customer_id: "customer-1",
  conversation_id: null,
  clinic_procedure_id: null,
  booking_date: "2026-03-01",
  booking_time: "14:00:00",
  status: "pending",
  total_amount: 500000,
  currency: "KRW",
  deposit_amount: null,
  remaining_amount: null,
  notes: null,
  cancellation_reason: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("useBookingStore", () => {
  beforeEach(() => {
    useBookingStore.setState({
      bookings: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchBookings", () => {
    it("fetches and stores bookings", async () => {
      mockGet.mockResolvedValueOnce([FAKE_BOOKING]);

      await useBookingStore.getState().fetchBookings(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/bookings", {
        token: FAKE_TOKEN,
      });
      expect(useBookingStore.getState().bookings).toEqual([FAKE_BOOKING]);
      expect(useBookingStore.getState().isLoading).toBe(false);
    });

    it("fetches with status filter", async () => {
      mockGet.mockResolvedValueOnce([]);

      await useBookingStore.getState().fetchBookings(FAKE_TOKEN, "confirmed");

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/bookings?status=confirmed",
        { token: FAKE_TOKEN },
      );
    });

    it("sets error on failure", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      await useBookingStore.getState().fetchBookings(FAKE_TOKEN);

      expect(useBookingStore.getState().error).toBe("Failed to load bookings");
      expect(useBookingStore.getState().isLoading).toBe(false);
    });
  });

  describe("cancelBooking", () => {
    it("cancels booking and refetches", async () => {
      const cancelled = { ...FAKE_BOOKING, status: "cancelled" };
      mockPost.mockResolvedValueOnce(cancelled);
      mockGet.mockResolvedValueOnce([cancelled]);

      await useBookingStore
        .getState()
        .cancelBooking(FAKE_TOKEN, "booking-1", "Changed plans");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/bookings/booking-1/cancel",
        { cancellation_reason: "Changed plans" },
        { token: FAKE_TOKEN },
      );
      expect(mockGet).toHaveBeenCalledWith("/api/v1/bookings", {
        token: FAKE_TOKEN,
      });
    });
  });

  describe("completeBooking", () => {
    it("completes booking and refetches", async () => {
      const completed = { ...FAKE_BOOKING, status: "completed" };
      mockPost.mockResolvedValueOnce(completed);
      mockGet.mockResolvedValueOnce([completed]);

      await useBookingStore
        .getState()
        .completeBooking(FAKE_TOKEN, "booking-1");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/bookings/booking-1/complete",
        {},
        { token: FAKE_TOKEN },
      );
    });
  });
});
