import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  AIPersona,
  MessengerAccount,
  MessengerAccountCreate,
  MessengerAccountUpdate,
} from "@/types/analytics";

interface Clinic {
  id: string;
  name: string;
  slug: string;
  phone: string | null;
  address: string | null;
  business_hours: Record<string, unknown> | null;
  commission_rate: number;
  settings: Record<string, unknown>;
}

interface SettingsState {
  clinic: Clinic | null;
  messengerAccounts: MessengerAccount[];
  aiPersonas: AIPersona[];
  isLoading: boolean;
  error: string | null;

  fetchClinic: (token: string) => Promise<void>;
  updateClinic: (
    token: string,
    data: Record<string, unknown>,
  ) => Promise<void>;
  fetchMessengerAccounts: (token: string) => Promise<void>;
  createMessengerAccount: (
    token: string,
    data: MessengerAccountCreate,
  ) => Promise<void>;
  updateMessengerAccount: (
    token: string,
    id: string,
    data: MessengerAccountUpdate,
  ) => Promise<void>;
  deleteMessengerAccount: (token: string, id: string) => Promise<void>;
  fetchAIPersonas: (token: string) => Promise<void>;
  createAIPersona: (
    token: string,
    data: { name: string; personality?: string; system_prompt?: string },
  ) => Promise<void>;
  updateAIPersona: (
    token: string,
    id: string,
    data: Record<string, unknown>,
  ) => Promise<void>;
  deleteAIPersona: (token: string, id: string) => Promise<void>;
  fetchAll: (token: string) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  clinic: null,
  messengerAccounts: [],
  aiPersonas: [],
  isLoading: false,
  error: null,

  fetchClinic: async (token) => {
    const data = await api.get<Clinic>("/api/v1/clinics/me", { token });
    set({ clinic: data });
  },

  updateClinic: async (token, data) => {
    const updated = await api.patch<Clinic>("/api/v1/clinics/me", data, {
      token,
    });
    set({ clinic: updated });
  },

  fetchMessengerAccounts: async (token) => {
    const data = await api.get<MessengerAccount[]>(
      "/api/v1/messenger-accounts",
      { token },
    );
    set({ messengerAccounts: data });
  },

  createMessengerAccount: async (token, data) => {
    await api.post<MessengerAccount>("/api/v1/messenger-accounts", data, {
      token,
    });
    await get().fetchMessengerAccounts(token);
  },

  updateMessengerAccount: async (token, id, data) => {
    await api.patch<MessengerAccount>(
      `/api/v1/messenger-accounts/${id}`,
      data,
      { token },
    );
    await get().fetchMessengerAccounts(token);
  },

  deleteMessengerAccount: async (token, id) => {
    await api.delete(`/api/v1/messenger-accounts/${id}`, { token });
    await get().fetchMessengerAccounts(token);
  },

  fetchAIPersonas: async (token) => {
    const data = await api.get<AIPersona[]>("/api/v1/ai-personas", {
      token,
    });
    set({ aiPersonas: data });
  },

  createAIPersona: async (token, data) => {
    await api.post<AIPersona>("/api/v1/ai-personas", data, { token });
    await get().fetchAIPersonas(token);
  },

  updateAIPersona: async (token, id, data) => {
    await api.patch<AIPersona>(`/api/v1/ai-personas/${id}`, data, {
      token,
    });
    await get().fetchAIPersonas(token);
  },

  deleteAIPersona: async (token, id) => {
    await api.delete(`/api/v1/ai-personas/${id}`, { token });
    await get().fetchAIPersonas(token);
  },

  fetchAll: async (token) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchClinic(token),
        get().fetchMessengerAccounts(token),
        get().fetchAIPersonas(token),
      ]);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load settings" });
    }
  },
}));
