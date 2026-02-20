import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePaymentStore } from "@/stores/payment";

const mockGet = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const FAKE_TOKEN = "test-token";

const FAKE_PAYMENT = {
  id: "payment-1",
  clinic_id: "clinic-1",
  booking_id: "booking-1",
  customer_id: "customer-1",
  payment_type: "deposit",
  amount: 100000,
  currency: "KRW",
  pg_provider: "stripe",
  pg_payment_id: null,
  payment_method: "card",
  payment_link: null,
  qr_code_url: null,
  link_expires_at: null,
  status: "completed",
  paid_at: "2026-01-01T12:00:00Z",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T12:00:00Z",
};

describe("usePaymentStore", () => {
  beforeEach(() => {
    usePaymentStore.setState({
      payments: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchPayments", () => {
    it("fetches and stores payments", async () => {
      mockGet.mockResolvedValueOnce([FAKE_PAYMENT]);

      await usePaymentStore.getState().fetchPayments(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/payments", {
        token: FAKE_TOKEN,
      });
      expect(usePaymentStore.getState().payments).toEqual([FAKE_PAYMENT]);
      expect(usePaymentStore.getState().isLoading).toBe(false);
    });

    it("fetches with booking_id filter", async () => {
      mockGet.mockResolvedValueOnce([FAKE_PAYMENT]);

      await usePaymentStore
        .getState()
        .fetchPayments(FAKE_TOKEN, "booking-1");

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/payments?booking_id=booking-1",
        { token: FAKE_TOKEN },
      );
    });

    it("sets error on failure", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      await usePaymentStore.getState().fetchPayments(FAKE_TOKEN);

      expect(usePaymentStore.getState().error).toBe("Failed to load payments");
      expect(usePaymentStore.getState().isLoading).toBe(false);
    });
  });
});
