import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useCRMStore } from "@/stores/crm";

const mockGet = vi.fn();
const mockPost = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const FAKE_TOKEN = "test-token";

const FAKE_EVENT = {
  id: "event-1",
  clinic_id: "clinic-1",
  customer_id: "customer-1",
  payment_id: null,
  booking_id: null,
  event_type: "follow_up",
  scheduled_at: "2026-03-01T10:00:00Z",
  executed_at: null,
  status: "scheduled",
  message_content: "Follow up message",
  response: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const FAKE_SURVEY = {
  id: "survey-1",
  clinic_id: "clinic-1",
  customer_id: "customer-1",
  booking_id: null,
  conversation_id: null,
  survey_round: 1,
  overall_score: 4,
  service_score: 5,
  result_score: 4,
  communication_score: 4,
  nps_score: 8,
  would_revisit: "yes",
  feedback_text: "Great service",
  created_at: "2026-01-01T00:00:00Z",
};

const FAKE_SUMMARY = {
  total_surveys: 10,
  avg_overall: 4.2,
  avg_service: 4.5,
  avg_result: 4.0,
  avg_communication: 4.1,
  avg_nps: 7.5,
};

describe("useCRMStore", () => {
  beforeEach(() => {
    useCRMStore.setState({
      events: [],
      surveys: [],
      surveySummary: null,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchEvents", () => {
    it("fetches and stores events", async () => {
      mockGet.mockResolvedValueOnce([FAKE_EVENT]);

      await useCRMStore.getState().fetchEvents(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/crm/events", {
        token: FAKE_TOKEN,
      });
      expect(useCRMStore.getState().events).toEqual([FAKE_EVENT]);
    });

    it("fetches with status filter", async () => {
      mockGet.mockResolvedValueOnce([]);

      await useCRMStore.getState().fetchEvents(FAKE_TOKEN, "scheduled");

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/crm/events?status=scheduled",
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("cancelEvent", () => {
    it("cancels event and refetches", async () => {
      const cancelled = { ...FAKE_EVENT, status: "cancelled" };
      mockPost.mockResolvedValueOnce(cancelled);
      mockGet.mockResolvedValueOnce([cancelled]);

      await useCRMStore.getState().cancelEvent(FAKE_TOKEN, "event-1");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/crm/events/event-1/cancel",
        {},
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("fetchSurveys", () => {
    it("fetches surveys", async () => {
      mockGet.mockResolvedValueOnce([FAKE_SURVEY]);

      await useCRMStore.getState().fetchSurveys(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/crm/surveys", {
        token: FAKE_TOKEN,
      });
      expect(useCRMStore.getState().surveys).toEqual([FAKE_SURVEY]);
    });

    it("fetches surveys by round", async () => {
      mockGet.mockResolvedValueOnce([FAKE_SURVEY]);

      await useCRMStore.getState().fetchSurveys(FAKE_TOKEN, 1);

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/crm/surveys?survey_round=1",
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("fetchAll", () => {
    it("fetches all data and sets loading states", async () => {
      mockGet.mockResolvedValueOnce([FAKE_EVENT]);
      mockGet.mockResolvedValueOnce([FAKE_SURVEY]);
      mockGet.mockResolvedValueOnce(FAKE_SUMMARY);

      await useCRMStore.getState().fetchAll(FAKE_TOKEN);

      expect(useCRMStore.getState().isLoading).toBe(false);
      expect(useCRMStore.getState().error).toBeNull();
    });

    it("sets error on failure", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      await useCRMStore.getState().fetchAll(FAKE_TOKEN);

      expect(useCRMStore.getState().error).toBe("Failed to load CRM data");
    });
  });
});
