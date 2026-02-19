import { create } from "zustand";

import { api } from "@/lib/api";
import type { Settlement } from "@/types/settlement";

interface SettlementState {
  settlements: Settlement[];
  selectedSettlement: Settlement | null;
  isLoading: boolean;
  error: string | null;

  fetchSettlements: (
    token: string,
    year?: number,
    month?: number,
  ) => Promise<void>;
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

  fetchSettlements: async (token, year, month) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams();
      if (year) params.set("year", String(year));
      if (month) params.set("month", String(month));
      const qs = params.toString() ? `?${params.toString()}` : "";
      const data = await api.get<Settlement[]>(
        `/api/v1/settlements${qs}`,
        { token },
      );
      set({ settlements: data, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load settlements" });
    }
  },

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
