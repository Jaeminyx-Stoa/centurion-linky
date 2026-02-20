import { create } from "zustand";

import { api, buildPaginationParams } from "@/lib/api";
import type { Customer, CustomerUpdate } from "@/types/customer";
import type { PaginatedResponse } from "@/types/api";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

interface CustomerState {
  customers: Customer[];
  selectedCustomer: Customer | null;
  isLoading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  total: number;

  fetchCustomers: (token: string) => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  fetchCustomer: (token: string, id: string) => Promise<void>;
  updateCustomer: (
    token: string,
    id: string,
    data: CustomerUpdate,
  ) => Promise<void>;
}

export const useCustomerStore = create<CustomerState>((set, get) => ({
  customers: [],
  selectedCustomer: null,
  isLoading: false,
  error: null,
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,

  fetchCustomers: async (token) => {
    set({ isLoading: true, error: null });
    try {
      const { page, pageSize } = get();
      const pagination = buildPaginationParams(page, pageSize);
      const data = await api.get<PaginatedResponse<Customer>>(
        `/api/v1/customers?${pagination}`,
        { token },
      );
      set({ customers: data.items, total: data.total, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load customers" });
    }
  },

  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),

  fetchCustomer: async (token, id) => {
    const data = await api.get<Customer>(`/api/v1/customers/${id}`, { token });
    set({ selectedCustomer: data });
  },

  updateCustomer: async (token, id, data) => {
    const updated = await api.patch<Customer>(
      `/api/v1/customers/${id}`,
      data,
      { token },
    );
    set({ selectedCustomer: updated });
    await get().fetchCustomers(token);
  },
}));
