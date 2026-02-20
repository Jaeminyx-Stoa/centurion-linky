import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useSettingsStore } from "@/stores/settings";

// Mock the api module
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

const FAKE_ACCOUNT = {
  id: "acc-1",
  clinic_id: "clinic-1",
  messenger_type: "telegram",
  account_name: "Test Bot",
  display_name: "Bot Display",
  webhook_url: "/api/webhooks/telegram/acc-1",
  target_countries: ["JP"],
  is_active: true,
  is_connected: false,
  last_synced_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("useSettingsStore — messenger account CRUD", () => {
  beforeEach(() => {
    useSettingsStore.setState({
      messengerAccounts: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchMessengerAccounts", () => {
    it("fetches and stores messenger accounts", async () => {
      mockGet.mockResolvedValueOnce([FAKE_ACCOUNT]);

      await useSettingsStore.getState().fetchMessengerAccounts(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith("/api/v1/messenger-accounts", {
        token: FAKE_TOKEN,
      });
      expect(useSettingsStore.getState().messengerAccounts).toEqual([
        FAKE_ACCOUNT,
      ]);
    });
  });

  describe("createMessengerAccount", () => {
    it("posts new account and refetches list", async () => {
      const createData = {
        messenger_type: "telegram",
        account_name: "New Bot",
        credentials: { bot_token: "123:ABC" },
      };
      mockPost.mockResolvedValueOnce(FAKE_ACCOUNT);
      mockGet.mockResolvedValueOnce([FAKE_ACCOUNT]);

      await useSettingsStore
        .getState()
        .createMessengerAccount(FAKE_TOKEN, createData);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/messenger-accounts",
        createData,
        { token: FAKE_TOKEN },
      );
      // Should refetch after create
      expect(mockGet).toHaveBeenCalledWith("/api/v1/messenger-accounts", {
        token: FAKE_TOKEN,
      });
      expect(useSettingsStore.getState().messengerAccounts).toEqual([
        FAKE_ACCOUNT,
      ]);
    });
  });

  describe("updateMessengerAccount", () => {
    it("patches account and refetches list", async () => {
      const updateData = { account_name: "Updated Bot", is_active: false };
      const updatedAccount = {
        ...FAKE_ACCOUNT,
        account_name: "Updated Bot",
        is_active: false,
      };
      mockPatch.mockResolvedValueOnce(updatedAccount);
      mockGet.mockResolvedValueOnce([updatedAccount]);

      await useSettingsStore
        .getState()
        .updateMessengerAccount(FAKE_TOKEN, "acc-1", updateData);

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/messenger-accounts/acc-1",
        updateData,
        { token: FAKE_TOKEN },
      );
      expect(mockGet).toHaveBeenCalledWith("/api/v1/messenger-accounts", {
        token: FAKE_TOKEN,
      });
      expect(useSettingsStore.getState().messengerAccounts[0].account_name).toBe(
        "Updated Bot",
      );
    });
  });

  describe("deleteMessengerAccount", () => {
    it("deletes account and refetches list", async () => {
      useSettingsStore.setState({ messengerAccounts: [FAKE_ACCOUNT] });
      mockDelete.mockResolvedValueOnce(undefined);
      mockGet.mockResolvedValueOnce([]);

      await useSettingsStore
        .getState()
        .deleteMessengerAccount(FAKE_TOKEN, "acc-1");

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/messenger-accounts/acc-1",
        { token: FAKE_TOKEN },
      );
      expect(mockGet).toHaveBeenCalledWith("/api/v1/messenger-accounts", {
        token: FAKE_TOKEN,
      });
      expect(useSettingsStore.getState().messengerAccounts).toEqual([]);
    });
  });
});
