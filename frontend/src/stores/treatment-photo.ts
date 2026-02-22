import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  TreatmentPhoto,
  TreatmentPhotoPaginated,
  PhotoPair,
} from "@/types/treatment-photo";

interface TreatmentPhotoStore {
  photos: TreatmentPhoto[];
  pairs: PhotoPair[];
  total: number;
  isLoading: boolean;
  fetchPhotos: (
    token: string,
    params?: {
      customer_id?: string;
      booking_id?: string;
      photo_type?: string;
      portfolio_only?: boolean;
    },
  ) => Promise<void>;
  fetchPairs: (token: string, customer_id?: string) => Promise<void>;
  approvePhoto: (token: string, photoId: string) => Promise<void>;
  deletePhoto: (token: string, photoId: string) => Promise<void>;
}

export const useTreatmentPhotoStore = create<TreatmentPhotoStore>((set) => ({
  photos: [],
  pairs: [],
  total: 0,
  isLoading: false,

  fetchPhotos: async (token, params) => {
    set({ isLoading: true });
    try {
      const qs = new URLSearchParams();
      if (params?.customer_id) qs.set("customer_id", params.customer_id);
      if (params?.booking_id) qs.set("booking_id", params.booking_id);
      if (params?.photo_type) qs.set("photo_type", params.photo_type);
      if (params?.portfolio_only) qs.set("portfolio_only", "true");
      const data = await api.get<TreatmentPhotoPaginated>(
        `/api/v1/treatment-photos/?${qs.toString()}`,
        { token },
      );
      set({ photos: data.items, total: data.total });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchPairs: async (token, customer_id) => {
    const qs = customer_id ? `?customer_id=${customer_id}` : "";
    const data = await api.get<PhotoPair[]>(
      `/api/v1/treatment-photos/pairs${qs}`,
      { token },
    );
    set({ pairs: data });
  },

  approvePhoto: async (token, photoId) => {
    await api.post(`/api/v1/treatment-photos/${photoId}/approve`, {
      token,
      body: {},
    });
  },

  deletePhoto: async (token, photoId) => {
    await api.delete(`/api/v1/treatment-photos/${photoId}`, { token });
  },
}));
