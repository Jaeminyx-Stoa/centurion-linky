import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useKnowledgeStore } from "@/stores/knowledge";

// Mock API
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

// Mock auth store
vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({ accessToken: "test-token" }),
}));

// Import page after mocks
import KnowledgePage from "@/app/(dashboard)/knowledge/page";

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
  is_verified: true,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

describe("KnowledgePage", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockImplementation((url: string) => {
      if (url.includes("response-library")) return Promise.resolve([FAKE_FAQ]);
      if (url.includes("medical-terms")) return Promise.resolve([FAKE_TERM]);
      return Promise.resolve([]);
    });
  });

  afterEach(() => {
    cleanup();
    useKnowledgeStore.setState({
      responseLibrary: [],
      medicalTerms: [],
      isLoading: false,
      error: null,
    });
  });

  it("renders tab sidebar with two tabs", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getAllByText("답변 라이브러리").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("의료 용어")).toBeInTheDocument();
    });
  });

  it("shows response library tab by default", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("보톡스 가격?")).toBeInTheDocument();
    });
  });

  it("displays FAQ entry with category badge", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getAllByText("가격").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("보톡스 가격?")).toBeInTheDocument();
      expect(screen.getByText("10만원부터")).toBeInTheDocument();
    });
  });

  it("displays FAQ tags", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("보톡스")).toBeInTheDocument();
    });
  });

  it("switches to medical terms tab", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("의료 용어")).toBeInTheDocument();
    });
    await user.click(screen.getByText("의료 용어"));

    await waitFor(() => {
      // Medical term should be visible
      expect(screen.getByText("주름 완화 시술")).toBeInTheDocument();
    });
  });

  it("shows verified badge on medical terms", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("의료 용어")).toBeInTheDocument();
    });
    await user.click(screen.getByText("의료 용어"));

    await waitFor(() => {
      expect(screen.getByText("인증")).toBeInTheDocument();
    });
  });

  it("shows translation previews on medical terms", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("의료 용어")).toBeInTheDocument();
    });
    await user.click(screen.getByText("의료 용어"));

    await waitFor(() => {
      expect(screen.getByText("en: Botox")).toBeInTheDocument();
    });
  });

  it("shows create form for response library when clicking add", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("보톡스 가격?")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /추가/ }));

    expect(screen.getByLabelText("질문")).toBeInTheDocument();
    expect(screen.getByLabelText("답변")).toBeInTheDocument();
  });

  it("hides create form on cancel", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("보톡스 가격?")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /추가/ }));
    expect(screen.getByLabelText("질문")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "취소" }));
    expect(screen.queryByLabelText("질문")).not.toBeInTheDocument();
  });

  it("shows empty state when no entries", async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes("response-library")) return Promise.resolve([]);
      if (url.includes("medical-terms")) return Promise.resolve([]);
      return Promise.resolve([]);
    });

    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("등록된 답변이 없습니다")).toBeInTheDocument();
    });
  });

  it("shows empty state for medical terms tab", async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes("response-library")) return Promise.resolve([]);
      if (url.includes("medical-terms")) return Promise.resolve([]);
      return Promise.resolve([]);
    });

    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("의료 용어")).toBeInTheDocument();
    });
    await user.click(screen.getByText("의료 용어"));

    await waitFor(() => {
      expect(
        screen.getByText("등록된 의료 용어가 없습니다"),
      ).toBeInTheDocument();
    });
  });

  it("creates a new FAQ entry", async () => {
    mockPost.mockResolvedValueOnce(FAKE_FAQ);
    mockGet.mockImplementation((url: string) => {
      if (url.includes("response-library")) return Promise.resolve([FAKE_FAQ]);
      if (url.includes("medical-terms")) return Promise.resolve([]);
      return Promise.resolve([]);
    });

    render(<KnowledgePage />);
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /추가/ }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /추가/ }));

    // Fill in form
    const questionInput = screen.getByLabelText("질문");
    const answerInput = screen.getByLabelText("답변");
    await user.type(questionInput, "새 질문");
    await user.type(answerInput, "새 답변");
    await user.click(screen.getByRole("button", { name: "생성" }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/response-library",
        expect.objectContaining({
          question: "새 질문",
          answer: "새 답변",
        }),
        { token: "test-token" },
      );
    });
  });

  it("shows error banner when fetchAll fails", async () => {
    mockGet.mockRejectedValue(new Error("Network error"));

    render(<KnowledgePage />);
    await waitFor(() => {
      expect(
        screen.getByText("지식 데이터 로딩 실패"),
      ).toBeInTheDocument();
    });
  });

  it("shows page title in sidebar", async () => {
    render(<KnowledgePage />);
    await waitFor(() => {
      expect(screen.getByText("지식 관리")).toBeInTheDocument();
    });
  });
});
