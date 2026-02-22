import { create } from "zustand";

import { api } from "@/lib/api";
import type { ConsultationProtocol } from "@/types/protocol";

interface ProtocolState {
  protocols: ConsultationProtocol[];
  isLoading: boolean;
  error: string | null;

  fetchProtocols: (token: string) => Promise<void>;
  createProtocol: (
    token: string,
    data: {
      name: string;
      procedure_id?: string;
      checklist_items: Array<{
        id: string;
        question_ko: string;
        required: boolean;
        type: string;
      }>;
    },
  ) => Promise<void>;
}

export const useProtocolStore = create<ProtocolState>((set, get) => ({
  protocols: [],
  isLoading: false,
  error: null,

  fetchProtocols: async (token) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.get<{ items: ConsultationProtocol[] }>(
        "/api/v1/protocols",
        { token },
      );
      set({ protocols: data.items, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load protocols" });
    }
  },

  createProtocol: async (token, data) => {
    await api.post("/api/v1/protocols", { token, body: data });
    await get().fetchProtocols(token);
  },
}));
