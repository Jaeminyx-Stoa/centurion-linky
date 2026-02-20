import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  ProcedureCategoryTree,
  Procedure,
  ClinicProcedure,
  ProcedurePricing,
} from "@/types/procedure";
import type {
  ProcedurePricingCreate,
  ProcedurePricingUpdate,
  ProcedureCategoryCreate,
} from "@/types/pricing";

interface ProcedureState {
  categories: ProcedureCategoryTree[];
  procedures: Procedure[];
  clinicProcedures: ClinicProcedure[];
  selectedClinicProcedure: ClinicProcedure | null;
  pricings: ProcedurePricing[];
  isLoading: boolean;
  error: string | null;

  fetchCategories: (token: string) => Promise<void>;
  fetchProcedures: (token: string, categoryId?: string) => Promise<void>;
  fetchClinicProcedures: (token: string) => Promise<void>;
  selectClinicProcedure: (token: string, id: string) => Promise<void>;
  fetchPricings: (token: string) => Promise<void>;
  createPricing: (token: string, data: ProcedurePricingCreate) => Promise<void>;
  updatePricing: (
    token: string,
    id: string,
    data: ProcedurePricingUpdate,
  ) => Promise<void>;
  deletePricing: (token: string, id: string) => Promise<void>;
  createCategory: (token: string, data: ProcedureCategoryCreate) => Promise<void>;
  updateCategory: (
    token: string,
    id: string,
    data: Record<string, unknown>,
  ) => Promise<void>;
  addClinicProcedure: (
    token: string,
    data: { procedure_id: string },
  ) => Promise<void>;
  updateClinicProcedure: (
    token: string,
    id: string,
    data: Record<string, unknown>,
  ) => Promise<void>;
}

export const useProcedureStore = create<ProcedureState>((set, get) => ({
  categories: [],
  procedures: [],
  clinicProcedures: [],
  selectedClinicProcedure: null,
  pricings: [],
  isLoading: false,
  error: null,

  fetchCategories: async (token) => {
    const data = await api.get<ProcedureCategoryTree[]>(
      "/api/v1/procedure-categories",
      { token },
    );
    set({ categories: data });
  },

  fetchProcedures: async (token, categoryId) => {
    const params = categoryId ? `?category_id=${categoryId}` : "";
    const data = await api.get<Procedure[]>(
      `/api/v1/procedures${params}`,
      { token },
    );
    set({ procedures: data });
  },

  fetchClinicProcedures: async (token) => {
    const data = await api.get<ClinicProcedure[]>(
      "/api/v1/clinic-procedures",
      { token },
    );
    set({ clinicProcedures: data });
  },

  selectClinicProcedure: async (token, id) => {
    set({ isLoading: true });
    const data = await api.get<ClinicProcedure>(
      `/api/v1/clinic-procedures/${id}`,
      { token },
    );
    set({ selectedClinicProcedure: data, isLoading: false });
  },

  fetchPricings: async (token) => {
    const data = await api.get<ProcedurePricing[]>("/api/v1/pricing", {
      token,
    });
    set({ pricings: data });
  },

  createPricing: async (token, data) => {
    await api.post<ProcedurePricing>("/api/v1/pricing", data, { token });
    await get().fetchPricings(token);
  },

  updatePricing: async (token, id, data) => {
    await api.patch<ProcedurePricing>(`/api/v1/pricing/${id}`, data, {
      token,
    });
    await get().fetchPricings(token);
  },

  deletePricing: async (token, id) => {
    await api.delete(`/api/v1/pricing/${id}`, { token });
    await get().fetchPricings(token);
  },

  createCategory: async (token, data) => {
    await api.post<ProcedureCategoryTree>(
      "/api/v1/procedure-categories",
      data,
      { token },
    );
    await get().fetchCategories(token);
  },

  updateCategory: async (token, id, data) => {
    await api.patch<ProcedureCategoryTree>(
      `/api/v1/procedure-categories/${id}`,
      data,
      { token },
    );
    await get().fetchCategories(token);
  },

  addClinicProcedure: async (token, data) => {
    await api.post<ClinicProcedure>("/api/v1/clinic-procedures", data, {
      token,
    });
    await get().fetchClinicProcedures(token);
  },

  updateClinicProcedure: async (token, id, data) => {
    const updated = await api.patch<ClinicProcedure>(
      `/api/v1/clinic-procedures/${id}`,
      data,
      { token },
    );
    set({ selectedClinicProcedure: updated });
    await get().fetchClinicProcedures(token);
  },
}));
