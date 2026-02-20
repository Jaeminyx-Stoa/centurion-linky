import { create } from "zustand";

import { api } from "@/lib/api";
import type { Customer, CustomerUpdate } from "@/types/customer";

interface CustomerState {
  customers: Customer[];
  selectedCustomer: Customer | null;
  isLoading: boolean;
  error: string | null;

  fetchCustomers: (token: string) => Promise<void>;
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

  fetchCustomers: async (token) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.get<Customer[]>("/api/v1/customers", { token });
      set({ customers: data, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load customers" });
    }
  },

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
