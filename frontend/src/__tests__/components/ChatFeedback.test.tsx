import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("@/lib/api", () => ({
  api: {
    post: vi.fn().mockResolvedValue({ status: "ok", feedback: { rating: "up" } }),
  },
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({ accessToken: "test-token" }),
}));

vi.mock("@/stores/conversation", () => ({
  useConversationStore: Object.assign(
    () => ({
      selectedId: "conv-1",
      selectedDetail: { status: "active", ai_mode: true },
      messages: [
        {
          id: "msg-ai-1",
          conversation_id: "conv-1",
          sender_type: "ai",
          content: "AI response text",
          content_type: "text",
          ai_metadata: null,
          translated_content: null,
          is_read: true,
          created_at: "2026-01-01T00:00:00Z",
        },
        {
          id: "msg-cust-1",
          conversation_id: "conv-1",
          sender_type: "customer",
          content: "Customer question",
          content_type: "text",
          ai_metadata: null,
          translated_content: null,
          is_read: true,
          created_at: "2026-01-01T00:00:01Z",
        },
      ],
      isLoading: false,
      sendMessage: vi.fn(),
      toggleAi: vi.fn(),
      resolveConversation: vi.fn(),
    }),
    {
      setState: vi.fn(),
    },
  ),
}));

import { ChatWindow } from "@/components/dashboard/chat-window";
import { api } from "@/lib/api";

describe("ChatWindow AI Feedback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows thumbs up/down buttons on AI messages only", () => {
    render(<ChatWindow />);

    // AI message should have feedback buttons
    const helpfulButtons = screen.getAllByTitle("도움이 됨");
    expect(helpfulButtons.length).toBe(1);

    const notHelpfulButtons = screen.getAllByTitle("도움이 안 됨");
    expect(notHelpfulButtons.length).toBe(1);
  });

  it("sends feedback when thumbs up is clicked", async () => {
    render(<ChatWindow />);

    const thumbsUp = screen.getByTitle("도움이 됨");
    fireEvent.click(thumbsUp);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        "/api/v1/conversations/conv-1/messages/msg-ai-1/feedback",
        { rating: "up" },
        { token: "test-token" },
      );
    });
  });

  it("shows thanks message after feedback", async () => {
    render(<ChatWindow />);

    const thumbsDown = screen.getByTitle("도움이 안 됨");
    fireEvent.click(thumbsDown);

    await waitFor(() => {
      expect(screen.getByText("피드백 감사합니다")).toBeInTheDocument();
    });
  });
});
