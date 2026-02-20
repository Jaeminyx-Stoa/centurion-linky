import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAILabStore } from "@/stores/ai-lab";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPatch = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
}));

const FAKE_TOKEN = "test-token";

const FAKE_AB_TEST = {
  id: "test-1",
  clinic_id: "clinic-1",
  name: "Persona Test",
  description: "Testing persona variants",
  test_type: "persona",
  status: "active",
  is_active: true,
  started_at: "2026-01-01T00:00:00Z",
  ended_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
  variants: [
    {
      id: "var-1",
      ab_test_id: "test-1",
      name: "Control",
      config: {},
      weight: 50,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "var-2",
      ab_test_id: "test-1",
      name: "Variant A",
      config: {},
      weight: 50,
      created_at: "2026-01-01T00:00:00Z",
    },
  ],
};

const FAKE_SIMULATION = {
  id: "sim-1",
  clinic_id: "clinic-1",
  persona_name: "Curious Tourist",
  persona_config: {},
  max_rounds: 10,
  actual_rounds: 5,
  status: "running",
  messages: null,
  started_at: "2026-01-01T00:00:00Z",
  completed_at: null,
  created_at: "2026-01-01T00:00:00Z",
  result: null,
};

const FAKE_PERSONA = {
  name: "Curious Tourist",
  profile: "A tourist looking for beauty treatments",
  behavior: "Asks many questions",
  language: "en",
  country: "US",
};

describe("useAILabStore", () => {
  beforeEach(() => {
    useAILabStore.setState({
      abTests: [],
      abTestStats: {},
      simulations: [],
      personas: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchABTests", () => {
    it("fetches and stores AB tests", async () => {
      mockGet.mockResolvedValueOnce([FAKE_AB_TEST]);

      await useAILabStore.getState().fetchABTests(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/ab-tests", {
        token: FAKE_TOKEN,
      });
      expect(useAILabStore.getState().abTests).toEqual([FAKE_AB_TEST]);
    });
  });

  describe("createABTest", () => {
    it("creates AB test and refetches", async () => {
      const createData = {
        name: "New Test",
        test_type: "persona",
        variants: [
          { name: "Control", config: {} },
          { name: "Variant A", config: {} },
        ],
      };
      mockPost.mockResolvedValueOnce(FAKE_AB_TEST);
      mockGet.mockResolvedValueOnce([FAKE_AB_TEST]);

      await useAILabStore.getState().createABTest(FAKE_TOKEN, createData);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/ab-tests",
        createData,
        { token: FAKE_TOKEN },
      );
      expect(mockGet).toHaveBeenCalledWith("/api/v1/ab-tests", {
        token: FAKE_TOKEN,
      });
    });
  });

  describe("fetchSimulations", () => {
    it("fetches simulations", async () => {
      mockGet.mockResolvedValueOnce([FAKE_SIMULATION]);

      await useAILabStore.getState().fetchSimulations(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/simulations", {
        token: FAKE_TOKEN,
      });
      expect(useAILabStore.getState().simulations).toEqual([FAKE_SIMULATION]);
    });
  });

  describe("fetchPersonas", () => {
    it("fetches personas", async () => {
      mockGet.mockResolvedValueOnce([FAKE_PERSONA]);

      await useAILabStore.getState().fetchPersonas(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/simulations/personas", {
        token: FAKE_TOKEN,
      });
      expect(useAILabStore.getState().personas).toEqual([FAKE_PERSONA]);
    });
  });

  describe("fetchAll", () => {
    it("fetches all data", async () => {
      mockGet.mockResolvedValueOnce([FAKE_AB_TEST]);
      mockGet.mockResolvedValueOnce([FAKE_SIMULATION]);
      mockGet.mockResolvedValueOnce([FAKE_PERSONA]);

      await useAILabStore.getState().fetchAll(FAKE_TOKEN);

      expect(useAILabStore.getState().isLoading).toBe(false);
      expect(useAILabStore.getState().error).toBeNull();
    });

    it("sets error on failure", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      await useAILabStore.getState().fetchAll(FAKE_TOKEN);

      expect(useAILabStore.getState().error).toBe(
        "Failed to load AI Lab data",
      );
    });
  });
});
