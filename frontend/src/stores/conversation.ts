import { create } from "zustand";

import { api, buildPaginationParams } from "@/lib/api";
import type {
  Conversation,
  ConversationDetail,
  Customer,
  Message,
} from "@/types/conversation";
import type { PaginatedResponse } from "@/types/api";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

interface ConversationState {
  conversations: Conversation[];
  selectedId: string | null;
  selectedDetail: ConversationDetail | null;
  messages: Message[];
  customer: Customer | null;
  isLoading: boolean;
  page: number;
  pageSize: number;
  total: number;

  fetchConversations: (token: string, status?: string) => Promise<void>;
  setPage: (page: number) => void;
  selectConversation: (token: string, id: string) => Promise<void>;
  fetchMessages: (token: string, conversationId: string) => Promise<void>;
  fetchCustomer: (token: string, customerId: string) => Promise<void>;
  sendMessage: (token: string, conversationId: string, content: string) => Promise<void>;
  toggleAi: (token: string, conversationId: string) => Promise<void>;
  resolveConversation: (token: string, conversationId: string) => Promise<void>;

  // WebSocket event handlers
  onNewMessage: (message: Message) => void;
  onConversationUpdate: (conversation: Partial<Conversation> & { id: string }) => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  selectedId: null,
  selectedDetail: null,
  messages: [],
  customer: null,
  isLoading: false,
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,

  fetchConversations: async (token, status) => {
    const { page, pageSize } = get();
    const pagination = buildPaginationParams(page, pageSize);
    const statusParam = status ? `&status=${status}` : "";
    const data = await api.get<PaginatedResponse<Conversation>>(
      `/api/v1/conversations?${pagination}${statusParam}`,
      { token },
    );
    set({ conversations: data.items, total: data.total });
  },

  setPage: (page) => set({ page }),

  selectConversation: async (token, id) => {
    set({ selectedId: id, isLoading: true });
    const [detail, messages] = await Promise.all([
      api.get<ConversationDetail>(`/api/v1/conversations/${id}`, { token }),
      api.get<Message[]>(`/api/v1/conversations/${id}/messages`, { token }),
    ]);
    set({ selectedDetail: detail, messages, isLoading: false });

    // Fetch customer
    get().fetchCustomer(token, detail.customer_id);

    // Update unread count in list
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === id ? { ...c, unread_count: 0 } : c,
      ),
    }));
  },

  fetchMessages: async (token, conversationId) => {
    const messages = await api.get<Message[]>(
      `/api/v1/conversations/${conversationId}/messages`,
      { token },
    );
    set({ messages });
  },

  fetchCustomer: async (token, customerId) => {
    const customer = await api.get<Customer>(
      `/api/v1/customers/${customerId}`,
      { token },
    );
    set({ customer });
  },

  sendMessage: async (token, conversationId, content) => {
    const message = await api.post<Message>(
      `/api/v1/conversations/${conversationId}/messages`,
      { content },
      { token },
    );
    set((state) => ({ messages: [...state.messages, message] }));
  },

  toggleAi: async (token, conversationId) => {
    const updated = await api.post<ConversationDetail>(
      `/api/v1/conversations/${conversationId}/toggle-ai`,
      {},
      { token },
    );
    set({ selectedDetail: updated });
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId ? { ...c, ai_mode: updated.ai_mode } : c,
      ),
    }));
  },

  resolveConversation: async (token, conversationId) => {
    const updated = await api.post<ConversationDetail>(
      `/api/v1/conversations/${conversationId}/resolve`,
      {},
      { token },
    );
    set({ selectedDetail: updated });
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId ? { ...c, status: updated.status } : c,
      ),
    }));
  },

  onNewMessage: (message) => {
    const { selectedId } = get();
    if (message.conversation_id === selectedId) {
      set((state) => ({ messages: [...state.messages, message] }));
    }
    // Update conversation list preview
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === message.conversation_id
          ? {
              ...c,
              last_message_preview: message.content.slice(0, 200),
              last_message_at: message.created_at,
              unread_count:
                c.id === selectedId || message.sender_type !== "customer"
                  ? c.unread_count
                  : c.unread_count + 1,
            }
          : c,
      ),
    }));
  },

  onConversationUpdate: (update) => {
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === update.id ? { ...c, ...update } : c,
      ),
    }));
    if (get().selectedId === update.id && get().selectedDetail) {
      set((state) => ({
        selectedDetail: state.selectedDetail
          ? { ...state.selectedDetail, ...update }
          : null,
      }));
    }
  },
}));
