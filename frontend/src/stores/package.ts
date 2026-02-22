import { create } from "zustand";

import { api } from "@/lib/api";
import type { ProcedurePackage, PackageEnrollment } from "@/types/package";

interface PackageState {
  packages: ProcedurePackage[];
  enrollments: PackageEnrollment[];
  isLoading: boolean;
  error: string | null;

  fetchPackages: (token: string) => Promise<void>;
  createPackage: (token: string, data: Partial<ProcedurePackage>) => Promise<void>;
  enrollCustomer: (
    token: string,
    packageId: string,
    customerId: string,
  ) => Promise<void>;
  fetchEnrollments: (token: string, packageId: string) => Promise<void>;
  completeSession: (
    token: string,
    enrollmentId: string,
    sessionNumber: number,
  ) => Promise<void>;
}

export const usePackageStore = create<PackageState>((set, get) => ({
  packages: [],
  enrollments: [],
  isLoading: false,
  error: null,

  fetchPackages: async (token) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.get<{ items: ProcedurePackage[] }>(
        "/api/v1/packages",
        { token },
      );
      set({ packages: data.items, isLoading: false });
    } catch {
      set({ isLoading: false, error: "Failed to load packages" });
    }
  },

  createPackage: async (token, data) => {
    await api.post("/api/v1/packages", { token, body: data });
    await get().fetchPackages(token);
  },

  enrollCustomer: async (token, packageId, customerId) => {
    await api.post(`/api/v1/packages/${packageId}/enroll`, {
      token,
      body: { customer_id: customerId },
    });
  },

  fetchEnrollments: async (token, packageId) => {
    const data = await api.get<{ items: PackageEnrollment[] }>(
      `/api/v1/packages/${packageId}/enrollments`,
      { token },
    );
    set({ enrollments: data.items });
  },

  completeSession: async (token, enrollmentId, sessionNumber) => {
    await api.post(
      `/api/v1/packages/enrollments/${enrollmentId}/sessions/${sessionNumber}/complete`,
      { token },
    );
  },
}));
