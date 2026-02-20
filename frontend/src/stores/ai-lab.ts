import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  ABTest,
  ABTestCreate,
  ABTestStats,
  SimulationSession,
  SimulationCreate,
  SimulationPersona,
} from "@/types/ai-lab";

interface AILabState {
  abTests: ABTest[];
  abTestStats: Record<string, ABTestStats[]>;
  simulations: SimulationSession[];
  personas: SimulationPersona[];
  isLoading: boolean;
  error: string | null;

  fetchABTests: (token: string) => Promise<void>;
  createABTest: (token: string, data: ABTestCreate) => Promise<void>;
  updateABTest: (
    token: string,
    id: string,
    data: Record<string, unknown>,
  ) => Promise<void>;
  fetchABTestStats: (token: string, testId: string) => Promise<void>;
  fetchSimulations: (token: string, status?: string) => Promise<void>;
  createSimulation: (token: string, data: SimulationCreate) => Promise<void>;
  completeSimulation: (token: string, id: string) => Promise<void>;
  fetchPersonas: (token: string) => Promise<void>;
  fetchAll: (token: string) => Promise<void>;
}

export const useAILabStore = create<AILabState>((set, get) => ({
  abTests: [],
  abTestStats: {},
  simulations: [],
  personas: [],
  isLoading: false,
  error: null,

  fetchABTests: async (token) => {
    const data = await api.get<ABTest[]>("/api/v1/ab-tests", { token });
    set({ abTests: data });
  },

  createABTest: async (token, data) => {
    await api.post<ABTest>("/api/v1/ab-tests", data, { token });
    await get().fetchABTests(token);
  },

  updateABTest: async (token, id, data) => {
    await api.patch<ABTest>(`/api/v1/ab-tests/${id}`, data, { token });
    await get().fetchABTests(token);
  },

  fetchABTestStats: async (token, testId) => {
    const data = await api.get<ABTestStats[]>(
      `/api/v1/ab-tests/${testId}/stats`,
      { token },
    );
    set((state) => ({
      abTestStats: { ...state.abTestStats, [testId]: data },
    }));
  },

  fetchSimulations: async (token, status) => {
    const params = status ? `?status=${status}` : "";
    const data = await api.get<SimulationSession[]>(
      `/api/v1/simulations${params}`,
      { token },
    );
    set({ simulations: data });
  },

  createSimulation: async (token, data) => {
    await api.post<SimulationSession>("/api/v1/simulations", data, { token });
    await get().fetchSimulations(token);
  },

  completeSimulation: async (token, id) => {
    await api.post<SimulationSession>(
      `/api/v1/simulations/${id}/complete`,
      {},
      { token },
    );
    await get().fetchSimulations(token);
  },

  fetchPersonas: async (token) => {
    const data = await api.get<SimulationPersona[]>(
      "/api/v1/simulations/personas",
      { token },
    );
    set({ personas: data });
  },

  fetchAll: async (token) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchABTests(token),
        get().fetchSimulations(token),
        get().fetchPersonas(token),
      ]);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load AI Lab data" });
    }
  },
}));
