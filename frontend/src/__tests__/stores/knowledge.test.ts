import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useKnowledgeStore } from "@/stores/knowledge";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPatch = vi.fn();
const mockDelete = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}));

const FAKE_TOKEN = "test-token";

const FAKE_FAQ = {
  id: "faq-1",
  clinic_id: "clinic-1",
  category: "pricing",
  subcategory: null,
  question: "보톡스 가격?",
  answer: "10만원부터",
  language_code: "ko",
  tags: ["보톡스"],
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

const FAKE_TERM = {
  id: "term-1",
  clinic_id: "clinic-1",
  term_ko: "보톡스",
  translations: { en: "Botox", ja: "ボトックス" },
  category: "procedure",
  description: "주름 완화 시술",
  is_verified: false,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

describe("useKnowledgeStore — response library CRUD", () => {
  beforeEach(() => {
    useKnowledgeStore.setState({
      responseLibrary: [],
      medicalTerms: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchResponseLibrary", () => {
    it("fetches and stores response library entries", async () => {
      mockGet.mockResolvedValueOnce([FAKE_FAQ]);

      await useKnowledgeStore.getState().fetchResponseLibrary(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/response-library", {
        token: FAKE_TOKEN,
      });
      expect(useKnowledgeStore.getState().responseLibrary).toEqual([FAKE_FAQ]);
    });

    it("passes category filter in query string", async () => {
      mockGet.mockResolvedValueOnce([FAKE_FAQ]);

      await useKnowledgeStore
        .getState()
        .fetchResponseLibrary(FAKE_TOKEN, "pricing");

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/response-library?category=pricing",
        { token: FAKE_TOKEN },
      );
    });

    it("passes search query in query string", async () => {
      mockGet.mockResolvedValueOnce([]);

      await useKnowledgeStore
        .getState()
        .fetchResponseLibrary(FAKE_TOKEN, undefined, "보톡스");

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("q="),
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("createResponseLibrary", () => {
    it("posts new entry and refetches", async () => {
      const createData = {
        category: "pricing",
        question: "필러 가격?",
        answer: "20만원",
      };
      mockPost.mockResolvedValueOnce(FAKE_FAQ);
      mockGet.mockResolvedValueOnce([FAKE_FAQ]);

      await useKnowledgeStore
        .getState()
        .createResponseLibrary(FAKE_TOKEN, createData);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/response-library",
        createData,
        { token: FAKE_TOKEN },
      );
      expect(mockGet).toHaveBeenCalled();
    });
  });

  describe("updateResponseLibrary", () => {
    it("patches entry and refetches", async () => {
      const updateData = { answer: "15만원부터" };
      mockPatch.mockResolvedValueOnce({ ...FAKE_FAQ, ...updateData });
      mockGet.mockResolvedValueOnce([{ ...FAKE_FAQ, ...updateData }]);

      await useKnowledgeStore
        .getState()
        .updateResponseLibrary(FAKE_TOKEN, "faq-1", updateData);

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/response-library/faq-1",
        updateData,
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("deleteResponseLibrary", () => {
    it("deletes entry and refetches", async () => {
      useKnowledgeStore.setState({ responseLibrary: [FAKE_FAQ] });
      mockDelete.mockResolvedValueOnce(undefined);
      mockGet.mockResolvedValueOnce([]);

      await useKnowledgeStore
        .getState()
        .deleteResponseLibrary(FAKE_TOKEN, "faq-1");

      expect(mockDelete).toHaveBeenCalledWith("/api/v1/response-library/faq-1", {
        token: FAKE_TOKEN,
      });
      expect(useKnowledgeStore.getState().responseLibrary).toEqual([]);
    });
  });
});

describe("useKnowledgeStore — medical terms CRUD", () => {
  beforeEach(() => {
    useKnowledgeStore.setState({
      responseLibrary: [],
      medicalTerms: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchMedicalTerms", () => {
    it("fetches and stores medical terms", async () => {
      mockGet.mockResolvedValueOnce([FAKE_TERM]);

      await useKnowledgeStore.getState().fetchMedicalTerms(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/medical-terms", {
        token: FAKE_TOKEN,
      });
      expect(useKnowledgeStore.getState().medicalTerms).toEqual([FAKE_TERM]);
    });
  });

  describe("createMedicalTerm", () => {
    it("posts new term and refetches", async () => {
      const createData = {
        term_ko: "필러",
        translations: { en: "Filler" },
        category: "material",
      };
      mockPost.mockResolvedValueOnce(FAKE_TERM);
      mockGet.mockResolvedValueOnce([FAKE_TERM]);

      await useKnowledgeStore
        .getState()
        .createMedicalTerm(FAKE_TOKEN, createData);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/medical-terms",
        createData,
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("deleteMedicalTerm", () => {
    it("deletes term and refetches", async () => {
      useKnowledgeStore.setState({ medicalTerms: [FAKE_TERM] });
      mockDelete.mockResolvedValueOnce(undefined);
      mockGet.mockResolvedValueOnce([]);

      await useKnowledgeStore
        .getState()
        .deleteMedicalTerm(FAKE_TOKEN, "term-1");

      expect(mockDelete).toHaveBeenCalledWith("/api/v1/medical-terms/term-1", {
        token: FAKE_TOKEN,
      });
      expect(useKnowledgeStore.getState().medicalTerms).toEqual([]);
    });
  });
});

describe("useKnowledgeStore — fetchAll", () => {
  beforeEach(() => {
    useKnowledgeStore.setState({
      responseLibrary: [],
      medicalTerms: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it("loads both datasets and sets isLoading", async () => {
    mockGet
      .mockResolvedValueOnce([FAKE_FAQ])
      .mockResolvedValueOnce([FAKE_TERM]);

    await useKnowledgeStore.getState().fetchAll(FAKE_TOKEN);

    const state = useKnowledgeStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("sets error on failure", async () => {
    mockGet.mockRejectedValueOnce(new Error("Network error"));

    await useKnowledgeStore.getState().fetchAll(FAKE_TOKEN);

    const state = useKnowledgeStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeTruthy();
  });
});
