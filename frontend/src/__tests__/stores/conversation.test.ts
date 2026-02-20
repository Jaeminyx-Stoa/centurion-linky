import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useConversationStore } from "@/stores/conversation";

const mockGet = vi.fn();
const mockPost = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
  buildPaginationParams: (page: number, pageSize: number) =>
    `limit=${pageSize}&offset=${(page - 1) * pageSize}`,
}));

const FAKE_TOKEN = "test-token";

const FAKE_CONVERSATION = {
  id: "conv-1",
  clinic_id: "clinic-1",
  customer_id: "cust-1",
  messenger_account_id: "acct-1",
  status: "active",
  ai_mode: true,
  satisfaction_score: null,
  satisfaction_level: null,
  last_message_at: "2026-01-01T00:00:00Z",
  last_message_preview: "Hello",
  unread_count: 3,
  created_at: "2026-01-01T00:00:00Z",
  customer_name: "Test Customer",
  customer_country: "JP",
  customer_language: "ja",
  messenger_type: "telegram",
};

const FAKE_MESSAGE = {
  id: "msg-1",
  conversation_id: "conv-1",
  sender_type: "customer",
  content: "Hello",
  content_type: "text",
  created_at: "2026-01-01T00:00:00Z",
};

describe("useConversationStore", () => {
  beforeEach(() => {
    useConversationStore.setState({
      conversations: [],
      selectedId: null,
      selectedDetail: null,
      messages: [],
      customer: null,
      isLoading: false,
      page: 1,
      pageSize: 20,
      total: 0,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchConversations", () => {
    it("fetches paginated conversations", async () => {
      mockGet.mockResolvedValueOnce({
        items: [FAKE_CONVERSATION],
        total: 1,
        limit: 20,
        offset: 0,
      });

      await useConversationStore.getState().fetchConversations(FAKE_TOKEN);

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/conversations?limit=20&offset=0",
        { token: FAKE_TOKEN },
      );
      expect(useConversationStore.getState().conversations).toHaveLength(1);
      expect(useConversationStore.getState().total).toBe(1);
    });

    it("fetches with status filter", async () => {
      mockGet.mockResolvedValueOnce({ items: [], total: 0, limit: 20, offset: 0 });

      await useConversationStore.getState().fetchConversations(FAKE_TOKEN, "active");

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/conversations?limit=20&offset=0&status=active",
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("setPage", () => {
    it("updates the page number", () => {
      useConversationStore.getState().setPage(3);
      expect(useConversationStore.getState().page).toBe(3);
    });
  });

  describe("sendMessage", () => {
    it("sends a message and adds to local state", async () => {
      useConversationStore.setState({ selectedId: "conv-1" });
      const sentMessage = { ...FAKE_MESSAGE, sender_type: "staff" };
      mockPost.mockResolvedValueOnce(sentMessage);

      await useConversationStore.getState().sendMessage(FAKE_TOKEN, "conv-1", "Hello back");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/conversations/conv-1/messages",
        { content: "Hello back" },
        { token: FAKE_TOKEN },
      );
    });
  });

  describe("onNewMessage (WebSocket)", () => {
    it("adds message to current conversation", () => {
      useConversationStore.setState({
        selectedId: "conv-1",
        messages: [],
        conversations: [FAKE_CONVERSATION],
      });

      useConversationStore.getState().onNewMessage({
        ...FAKE_MESSAGE,
        conversation_id: "conv-1",
      });

      expect(useConversationStore.getState().messages).toHaveLength(1);
    });

    it("updates unread count for other conversations", () => {
      useConversationStore.setState({
        selectedId: "conv-2",
        messages: [],
        conversations: [{ ...FAKE_CONVERSATION, id: "conv-1", unread_count: 0 }],
      });

      useConversationStore.getState().onNewMessage({
        ...FAKE_MESSAGE,
        conversation_id: "conv-1",
      });

      const conv = useConversationStore.getState().conversations.find((c) => c.id === "conv-1");
      expect(conv?.unread_count).toBe(1);
    });
  });

  describe("toggleAi", () => {
    it("toggles AI mode", async () => {
      const toggled = { ...FAKE_CONVERSATION, ai_mode: false };
      mockPost.mockResolvedValueOnce(toggled);

      await useConversationStore.getState().toggleAi(FAKE_TOKEN, "conv-1");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/conversations/conv-1/toggle-ai",
        {},
        { token: FAKE_TOKEN },
      );
    });
  });
});
