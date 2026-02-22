import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  FollowupRule,
  FollowupRuleCreate,
  SideEffectKeyword,
  SideEffectKeywordCreate,
  SideEffectAlert,
} from "@/types/followup";

interface FollowupState {
  rules: FollowupRule[];
  keywords: SideEffectKeyword[];
  alerts: SideEffectAlert[];
  isLoading: boolean;
  error: string | null;

  fetchRules: (token: string, procedureId?: string) => Promise<void>;
  createRule: (token: string, data: FollowupRuleCreate) => Promise<void>;
  deleteRule: (token: string, ruleId: string) => Promise<void>;
  fetchKeywords: (token: string) => Promise<void>;
  createKeywords: (token: string, data: SideEffectKeywordCreate) => Promise<void>;
  fetchAlerts: (token: string, days?: number) => Promise<void>;
}

export const useFollowupStore = create<FollowupState>((set) => ({
  rules: [],
  keywords: [],
  alerts: [],
  isLoading: false,
  error: null,

  fetchRules: async (token, procedureId) => {
    set({ isLoading: true, error: null });
    try {
      const params = procedureId ? `?procedure_id=${procedureId}` : "";
      const data = await api.get<FollowupRule[]>(
        `/api/v1/followups/rules${params}`,
        { token },
      );
      set({ rules: data, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load followup rules" });
    }
  },

  createRule: async (token, data) => {
    const rule = await api.post<FollowupRule>("/api/v1/followups/rules", {
      token,
      body: data,
    });
    set((s) => ({ rules: [...s.rules, rule] }));
  },

  deleteRule: async (token, ruleId) => {
    await api.delete(`/api/v1/followups/rules/${ruleId}`, { token });
    set((s) => ({ rules: s.rules.filter((r) => r.id !== ruleId) }));
  },

  fetchKeywords: async (token) => {
    const data = await api.get<SideEffectKeyword[]>(
      "/api/v1/followups/keywords",
      { token },
    );
    set({ keywords: data });
  },

  createKeywords: async (token, data) => {
    const kw = await api.post<SideEffectKeyword>(
      "/api/v1/followups/keywords",
      { token, body: data },
    );
    set((s) => ({ keywords: [...s.keywords, kw] }));
  },

  fetchAlerts: async (token, days = 7) => {
    const data = await api.get<SideEffectAlert[]>(
      `/api/v1/followups/alerts?days=${days}`,
      { token },
    );
    set({ alerts: data });
  },
}));
