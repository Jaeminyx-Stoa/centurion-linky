import { create } from "zustand";

import { api } from "@/lib/api";
import type { CRMEvent, SatisfactionSurvey, SurveySummary } from "@/types/crm";

interface CRMState {
  events: CRMEvent[];
  surveys: SatisfactionSurvey[];
  surveySummary: SurveySummary | null;
  isLoading: boolean;
  error: string | null;

  fetchEvents: (token: string, status?: string) => Promise<void>;
  cancelEvent: (token: string, id: string) => Promise<void>;
  fetchSurveys: (token: string, round?: number) => Promise<void>;
  fetchSurveySummary: (token: string) => Promise<void>;
  fetchAll: (token: string) => Promise<void>;
}

export const useCRMStore = create<CRMState>((set, get) => ({
  events: [],
  surveys: [],
  surveySummary: null,
  isLoading: false,
  error: null,

  fetchEvents: async (token, status) => {
    const params = status ? `?status=${status}` : "";
    const data = await api.get<CRMEvent[]>(`/api/v1/crm/events${params}`, {
      token,
    });
    set({ events: data });
  },

  cancelEvent: async (token, id) => {
    await api.post<CRMEvent>(`/api/v1/crm/events/${id}/cancel`, {}, {
      token,
    });
    await get().fetchEvents(token);
  },

  fetchSurveys: async (token, round) => {
    const params = round ? `?survey_round=${round}` : "";
    const data = await api.get<SatisfactionSurvey[]>(
      `/api/v1/crm/surveys${params}`,
      { token },
    );
    set({ surveys: data });
  },

  fetchSurveySummary: async (token) => {
    const data = await api.get<SurveySummary>("/api/v1/crm/surveys/summary", {
      token,
    });
    set({ surveySummary: data });
  },

  fetchAll: async (token) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchEvents(token),
        get().fetchSurveys(token),
        get().fetchSurveySummary(token),
      ]);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load CRM data" });
    }
  },
}));
