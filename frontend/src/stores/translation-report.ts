import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  TranslationReport,
  TranslationReportPaginated,
  TranslationQAStats,
} from "@/types/translation-report";

interface TranslationReportStore {
  reports: TranslationReport[];
  total: number;
  stats: TranslationQAStats | null;
  isLoading: boolean;
  fetchReports: (
    token: string,
    params?: { status?: string; severity?: string },
  ) => Promise<void>;
  fetchStats: (token: string, days?: number) => Promise<void>;
  createReport: (
    token: string,
    data: {
      source_language: string;
      target_language: string;
      original_text: string;
      translated_text: string;
      error_type: string;
      severity: string;
      message_id?: string;
      corrected_text?: string;
    },
  ) => Promise<void>;
  reviewReport: (
    token: string,
    reportId: string,
    data: { status: string; reviewer_notes?: string; corrected_text?: string },
  ) => Promise<void>;
}

export const useTranslationReportStore = create<TranslationReportStore>(
  (set) => ({
    reports: [],
    total: 0,
    stats: null,
    isLoading: false,

    fetchReports: async (token, params) => {
      set({ isLoading: true });
      try {
        const qs = new URLSearchParams();
        if (params?.status) qs.set("status", params.status);
        if (params?.severity) qs.set("severity", params.severity);
        const data = await api.get<TranslationReportPaginated>(
          `/api/v1/translation-reports/?${qs.toString()}`,
          { token },
        );
        set({ reports: data.items, total: data.total });
      } finally {
        set({ isLoading: false });
      }
    },

    fetchStats: async (token, days = 30) => {
      const data = await api.get<TranslationQAStats>(
        `/api/v1/translation-reports/stats?days=${days}`,
        { token },
      );
      set({ stats: data });
    },

    createReport: async (token, data) => {
      await api.post("/api/v1/translation-reports/", { token, body: data });
    },

    reviewReport: async (token, reportId, data) => {
      await api.patch(`/api/v1/translation-reports/${reportId}/review`, {
        token,
        body: data,
      });
    },
  }),
);
