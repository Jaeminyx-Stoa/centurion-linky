import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  CRMDashboard,
  SatisfactionTrend,
  NPSData,
  RevisitRate,
  AnalyticsOverview,
  ConsultationPerformance,
  SatisfactionScore,
} from "@/types/analytics";

interface CRMEvent {
  id: string;
  event_type: string;
  status: string;
  scheduled_at: string;
  [key: string]: unknown;
}

interface AnalyticsState {
  dashboard: CRMDashboard | null;
  satisfactionTrend: SatisfactionTrend[];
  nps: NPSData | null;
  revisitRate: RevisitRate | null;
  overview: AnalyticsOverview | null;
  consultationPerformance: ConsultationPerformance | null;
  satisfactionAlerts: SatisfactionScore[];
  crmEvents: CRMEvent[];
  isLoading: boolean;
  error: string | null;

  fetchDashboard: (token: string) => Promise<void>;
  fetchSatisfactionTrend: (token: string) => Promise<void>;
  fetchNPS: (token: string) => Promise<void>;
  fetchRevisitRate: (token: string) => Promise<void>;
  fetchOverview: (token: string) => Promise<void>;
  fetchConsultationPerformance: (
    token: string,
    year: number,
    month: number,
  ) => Promise<void>;
  fetchSatisfactionAlerts: (token: string) => Promise<void>;
  fetchCRMEvents: (token: string) => Promise<void>;
  fetchAll: (token: string) => Promise<void>;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  dashboard: null,
  satisfactionTrend: [],
  nps: null,
  revisitRate: null,
  overview: null,
  consultationPerformance: null,
  satisfactionAlerts: [],
  crmEvents: [],
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

  fetchOverview: async (token) => {
    const data = await api.get<AnalyticsOverview>(
      "/api/v1/analytics/overview",
      { token },
    );
    set({ overview: data });
  },

  fetchConsultationPerformance: async (token, year, month) => {
    const data = await api.get<ConsultationPerformance>(
      `/api/v1/analytics/consultation-performance?year=${year}&month=${month}`,
      { token },
    );
    set({ consultationPerformance: data });
  },

  fetchSatisfactionAlerts: async (token) => {
    const data = await api.get<SatisfactionScore[]>(
      "/api/v1/satisfaction/alerts",
      { token },
    );
    set({ satisfactionAlerts: data });
  },

  fetchCRMEvents: async (token) => {
    const data = await api.get<CRMEvent[]>("/api/v1/crm/events", { token });
    set({ crmEvents: data });
  },

  fetchAll: async (token) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchDashboard(token),
        get().fetchSatisfactionTrend(token),
        get().fetchNPS(token),
        get().fetchRevisitRate(token),
        get().fetchOverview(token),
      ]);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load analytics" });
    }
  },
}));
