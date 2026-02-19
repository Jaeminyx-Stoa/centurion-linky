import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  CRMDashboard,
  SatisfactionTrend,
  NPSData,
  RevisitRate,
} from "@/types/analytics";

interface AnalyticsState {
  dashboard: CRMDashboard | null;
  satisfactionTrend: SatisfactionTrend[];
  nps: NPSData | null;
  revisitRate: RevisitRate | null;
  isLoading: boolean;
  error: string | null;

  fetchDashboard: (token: string) => Promise<void>;
  fetchSatisfactionTrend: (token: string) => Promise<void>;
  fetchNPS: (token: string) => Promise<void>;
  fetchRevisitRate: (token: string) => Promise<void>;
  fetchAll: (token: string) => Promise<void>;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  dashboard: null,
  satisfactionTrend: [],
  nps: null,
  revisitRate: null,
  isLoading: false,
  error: null,

  fetchDashboard: async (token) => {
    const data = await api.get<CRMDashboard>("/api/v1/crm/dashboard", {
      token,
    });
    set({ dashboard: data });
  },

  fetchSatisfactionTrend: async (token) => {
    const data = await api.get<SatisfactionTrend[]>(
      "/api/v1/crm/satisfaction-trend",
      { token },
    );
    set({ satisfactionTrend: data });
  },

  fetchNPS: async (token) => {
    const data = await api.get<NPSData>("/api/v1/crm/nps", { token });
    set({ nps: data });
  },

  fetchRevisitRate: async (token) => {
    const data = await api.get<RevisitRate>("/api/v1/crm/revisit-rate", {
      token,
    });
    set({ revisitRate: data });
  },

  fetchAll: async (token) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchDashboard(token),
        get().fetchSatisfactionTrend(token),
        get().fetchNPS(token),
        get().fetchRevisitRate(token),
      ]);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load analytics" });
    }
  },
}));
