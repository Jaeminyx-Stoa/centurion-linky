import { create } from "zustand";

import { api, buildPaginationParams } from "@/lib/api";
import type { Settlement } from "@/types/settlement";
import type { PaginatedResponse } from "@/types/api";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

interface SettlementState {
  settlements: Settlement[];
  selectedSettlement: Settlement | null;
  isLoading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  total: number;

  fetchSettlements: (
    token: string,
    year?: number,
    month?: number,
  ) => Promise<void>;
  setPage: (page: number) => void;
  selectSettlement: (token: string, id: string) => Promise<void>;
  generateSettlement: (
    token: string,
    data: { year: number; month: number },
  ) => Promise<void>;
  confirmSettlement: (token: string, id: string) => Promise<void>;
  markPaid: (token: string, id: string) => Promise<void>;
}

export const useSettlementStore = create<SettlementState>((set, get) => ({
  settlements: [],
  selectedSettlement: null,
  isLoading: false,
  error: null,
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,

  fetchSettlements: async (token, year, month) => {
    set({ isLoading: true, error: null });
    try {
      const { page, pageSize } = get();
      const pagination = buildPaginationParams(page, pageSize);
      const params = new URLSearchParams(pagination.split("&").reduce((acc, p) => {
        const [k, v] = p.split("=");
        acc[k] = v;
        return acc;
      }, {} as Record<string, string>));
      if (year) params.set("year", String(year));
      if (month) params.set("month", String(month));
      const data = await api.get<PaginatedResponse<Settlement>>(
        `/api/v1/settlements?${params.toString()}`,
        { token },
      );
      set({ settlements: data.items, total: data.total, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load settlements" });
    }
  },

  setPage: (page) => set({ page }),

  selectSettlement: async (token, id) => {
    const data = await api.get<Settlement>(`/api/v1/settlements/${id}`, {
      token,
    });
    set({ selectedSettlement: data });
  },

  generateSettlement: async (token, data) => {
    set({ isLoading: true, error: null });
    try {
      await api.post<Settlement>("/api/v1/settlements/generate", data, {
        token,
      });
      await get().fetchSettlements(token, data.year, data.month);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to generate settlement" });
    }
  },

  confirmSettlement: async (token, id) => {
    const updated = await api.patch<Settlement>(
      `/api/v1/settlements/${id}/confirm`,
      {},
      { token },
    );
    set({ selectedSettlement: updated });
    set((state) => ({
      settlements: state.settlements.map((s) =>
        s.id === id ? updated : s,
      ),
    }));
  },

  markPaid: async (token, id) => {
    const updated = await api.patch<Settlement>(
      `/api/v1/settlements/${id}/mark-paid`,
      {},
      { token },
    );
    set({ selectedSettlement: updated });
    set((state) => ({
      settlements: state.settlements.map((s) =>
        s.id === id ? updated : s,
      ),
    }));
  },
}));
