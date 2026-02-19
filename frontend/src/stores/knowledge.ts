import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  MedicalTerm,
  MedicalTermCreate,
  MedicalTermUpdate,
  ResponseLibrary,
  ResponseLibraryCreate,
  ResponseLibraryUpdate,
} from "@/types/knowledge";

interface KnowledgeState {
  responseLibrary: ResponseLibrary[];
  medicalTerms: MedicalTerm[];
  isLoading: boolean;
  error: string | null;

  fetchResponseLibrary: (
    token: string,
    category?: string,
    q?: string,
  ) => Promise<void>;
  createResponseLibrary: (
    token: string,
    data: ResponseLibraryCreate,
  ) => Promise<void>;
  updateResponseLibrary: (
    token: string,
    id: string,
    data: ResponseLibraryUpdate,
  ) => Promise<void>;
  deleteResponseLibrary: (token: string, id: string) => Promise<void>;

  fetchMedicalTerms: (
    token: string,
    category?: string,
    q?: string,
  ) => Promise<void>;
  createMedicalTerm: (
    token: string,
    data: MedicalTermCreate,
  ) => Promise<void>;
  updateMedicalTerm: (
    token: string,
    id: string,
    data: MedicalTermUpdate,
  ) => Promise<void>;
  deleteMedicalTerm: (token: string, id: string) => Promise<void>;

  fetchAll: (token: string) => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  responseLibrary: [],
  medicalTerms: [],
  isLoading: false,
  error: null,

  fetchResponseLibrary: async (token, category?, q?) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (q) params.set("q", q);
    const qs = params.toString();
    const path = `/api/v1/response-library${qs ? `?${qs}` : ""}`;
    const data = await api.get<ResponseLibrary[]>(path, { token });
    set({ responseLibrary: data });
  },

  createResponseLibrary: async (token, data) => {
    await api.post<ResponseLibrary>("/api/v1/response-library", data, {
      token,
    });
    await get().fetchResponseLibrary(token);
  },

  updateResponseLibrary: async (token, id, data) => {
    await api.patch<ResponseLibrary>(
      `/api/v1/response-library/${id}`,
      data,
      { token },
    );
    await get().fetchResponseLibrary(token);
  },

  deleteResponseLibrary: async (token, id) => {
    await api.delete(`/api/v1/response-library/${id}`, { token });
    await get().fetchResponseLibrary(token);
  },

  fetchMedicalTerms: async (token, category?, q?) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (q) params.set("q", q);
    const qs = params.toString();
    const path = `/api/v1/medical-terms${qs ? `?${qs}` : ""}`;
    const data = await api.get<MedicalTerm[]>(path, { token });
    set({ medicalTerms: data });
  },

  createMedicalTerm: async (token, data) => {
    await api.post<MedicalTerm>("/api/v1/medical-terms", data, { token });
    await get().fetchMedicalTerms(token);
  },

  updateMedicalTerm: async (token, id, data) => {
    await api.patch<MedicalTerm>(`/api/v1/medical-terms/${id}`, data, {
      token,
    });
    await get().fetchMedicalTerms(token);
  },

  deleteMedicalTerm: async (token, id) => {
    await api.delete(`/api/v1/medical-terms/${id}`, { token });
    await get().fetchMedicalTerms(token);
  },

  fetchAll: async (token) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchResponseLibrary(token),
        get().fetchMedicalTerms(token),
      ]);
      set({ isLoading: false });
    } catch {
      set({ isLoading: false, error: "지식 데이터 로딩 실패" });
    }
  },
}));
