import { create } from "zustand";

import { api, buildPaginationParams } from "@/lib/api";
import type { CRMEvent, SatisfactionSurvey, SurveySummary } from "@/types/crm";
import type { PaginatedResponse } from "@/types/api";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

interface CRMState {
  events: CRMEvent[];
  surveys: SatisfactionSurvey[];
  surveySummary: SurveySummary | null;
  isLoading: boolean;
  error: string | null;
  eventsPage: number;
  eventsPageSize: number;
  eventsTotal: number;
  surveysPage: number;
  surveysPageSize: number;
  surveysTotal: number;

  fetchEvents: (token: string, status?: string) => Promise<void>;
  setEventsPage: (page: number) => void;
  cancelEvent: (token: string, id: string) => Promise<void>;
  fetchSurveys: (token: string, round?: number) => Promise<void>;
  setSurveysPage: (page: number) => void;
  fetchSurveySummary: (token: string) => Promise<void>;
  fetchAll: (token: string) => Promise<void>;
}

export const useCRMStore = create<CRMState>((set, get) => ({
  events: [],
  surveys: [],
  surveySummary: null,
  isLoading: false,
  error: null,
  eventsPage: 1,
  eventsPageSize: DEFAULT_PAGE_SIZE,
  eventsTotal: 0,
  surveysPage: 1,
  surveysPageSize: DEFAULT_PAGE_SIZE,
  surveysTotal: 0,

  fetchEvents: async (token, status) => {
    const { eventsPage, eventsPageSize } = get();
    const pagination = buildPaginationParams(eventsPage, eventsPageSize);
    const statusParam = status ? `&status=${status}` : "";
    const data = await api.get<PaginatedResponse<CRMEvent>>(
      `/api/v1/crm/events?${pagination}${statusParam}`,
      { token },
    );
    set({ events: data.items, eventsTotal: data.total });
  },

  setEventsPage: (page) => set({ eventsPage: page }),

  cancelEvent: async (token, id) => {
    await api.post<CRMEvent>(`/api/v1/crm/events/${id}/cancel`, {}, {
      token,
    });
    await get().fetchEvents(token);
  },

  fetchSurveys: async (token, round) => {
    const { surveysPage, surveysPageSize } = get();
    const pagination = buildPaginationParams(surveysPage, surveysPageSize);
    const roundParam = round ? `&survey_round=${round}` : "";
    const data = await api.get<PaginatedResponse<SatisfactionSurvey>>(
      `/api/v1/crm/surveys?${pagination}${roundParam}`,
      { token },
    );
    set({ surveys: data.items, surveysTotal: data.total });
  },

  setSurveysPage: (page) => set({ surveysPage: page }),

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
