import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useSettingsStore } from "@/stores/settings";

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
import SettingsPage from "@/app/(dashboard)/settings/page";

const FAKE_ACCOUNT = {
  id: "acc-1",
  clinic_id: "clinic-1",
  messenger_type: "telegram",
  account_name: "테스트 봇",
  display_name: "Beauty Bot",
  webhook_url: "/api/webhooks/telegram/acc-1",
  target_countries: null,
  is_active: true,
  is_connected: false,
  last_synced_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

const FAKE_CLINIC = {
  id: "clinic-1",
  name: "테스트의원",
  slug: "test-clinic",
  phone: null,
  address: null,
  business_hours: null,
  commission_rate: 10,
  settings: {},
};

describe("MessengerTab", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    // Setup default API responses for fetchAll
    mockGet.mockImplementation((url: string) => {
      if (url.includes("clinics")) return Promise.resolve(FAKE_CLINIC);
      if (url.includes("messenger")) return Promise.resolve([FAKE_ACCOUNT]);
      if (url.includes("persona")) return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  afterEach(() => {
    cleanup();
    useSettingsStore.setState({
      clinic: null,
      messengerAccounts: [],
      aiPersonas: [],
      isLoading: false,
      error: null,
    });
  });

  async function renderAndNavigateToMessengerTab() {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText("메신저 계정")).toBeInTheDocument();
    });
    await user.click(screen.getByText("메신저 계정"));
  }

  it("displays messenger accounts list", async () => {
    await renderAndNavigateToMessengerTab();

    expect(screen.getByText("테스트 봇")).toBeInTheDocument();
    expect(screen.getByText(/Telegram — Beauty Bot/)).toBeInTheDocument();
    expect(screen.getByText("활성")).toBeInTheDocument();
  });

  it("shows empty state when no accounts", async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes("clinics")) return Promise.resolve(FAKE_CLINIC);
      if (url.includes("messenger")) return Promise.resolve([]);
      if (url.includes("persona")) return Promise.resolve([]);
      return Promise.resolve([]);
    });

    await renderAndNavigateToMessengerTab();

    expect(
      screen.getByText("연동된 메신저 계정이 없습니다"),
    ).toBeInTheDocument();
  });

  it("shows create form when clicking add button", async () => {
    await renderAndNavigateToMessengerTab();

    await user.click(screen.getByRole("button", { name: /추가/ }));

    expect(screen.getByText("플랫폼")).toBeInTheDocument();
    expect(screen.getByText("Telegram")).toBeInTheDocument();
    expect(screen.getByText("Instagram")).toBeInTheDocument();
    expect(screen.getByText("LINE")).toBeInTheDocument();
    expect(screen.getByLabelText("계정 이름")).toBeInTheDocument();
    expect(screen.getByLabelText("Bot Token")).toBeInTheDocument();
  });

  it("switches credential fields when platform changes", async () => {
    await renderAndNavigateToMessengerTab();
    await user.click(screen.getByRole("button", { name: /추가/ }));

    // Default is Telegram — should show Bot Token
    expect(screen.getByLabelText("Bot Token")).toBeInTheDocument();

    // Switch to WhatsApp
    await user.click(screen.getByText("WhatsApp"));

    expect(screen.getByLabelText("Access Token")).toBeInTheDocument();
    expect(screen.getByLabelText("Phone Number ID")).toBeInTheDocument();
    // Bot Token should be gone
    expect(screen.queryByLabelText("Bot Token")).not.toBeInTheDocument();
  });

  it("creates a new account", async () => {
    const newAccount = {
      ...FAKE_ACCOUNT,
      id: "acc-2",
      account_name: "새 봇",
    };
    mockPost.mockResolvedValueOnce(newAccount);
    // After create, refetch returns updated list
    mockGet.mockImplementation((url: string) => {
      if (url.includes("clinics")) return Promise.resolve(FAKE_CLINIC);
      if (url.includes("messenger"))
        return Promise.resolve([FAKE_ACCOUNT, newAccount]);
      if (url.includes("persona")) return Promise.resolve([]);
      return Promise.resolve([]);
    });

    await renderAndNavigateToMessengerTab();
    await user.click(screen.getByRole("button", { name: /추가/ }));

    await user.type(screen.getByLabelText("계정 이름"), "새 봇");
    await user.type(screen.getByLabelText("Bot Token"), "999:XYZ");
    await user.click(screen.getByRole("button", { name: "생성" }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/messenger-accounts",
        expect.objectContaining({
          messenger_type: "telegram",
          account_name: "새 봇",
          credentials: { bot_token: "999:XYZ" },
        }),
        { token: "test-token" },
      );
    });
  });

  it("shows inline edit form when clicking edit button", async () => {
    await renderAndNavigateToMessengerTab();

    // Find and click pencil (edit) button — it's the first small icon button
    const editButtons = screen.getAllByRole("button").filter((btn) => {
      return btn.querySelector("svg.h-3\\.5");
    });
    // The first icon button in the account row should be edit
    await user.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByLabelText("계정 이름")).toBeInTheDocument();
      expect(screen.getByDisplayValue("테스트 봇")).toBeInTheDocument();
      expect(screen.getByLabelText("표시 이름")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "저장" })).toBeInTheDocument();
    });
  });

  it("hides create form on cancel", async () => {
    await renderAndNavigateToMessengerTab();

    await user.click(screen.getByRole("button", { name: /추가/ }));
    expect(screen.getByLabelText("계정 이름")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "취소" }));

    expect(screen.queryByLabelText("계정 이름")).not.toBeInTheDocument();
  });
});
