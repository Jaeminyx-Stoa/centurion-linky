import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  MedicalDocument,
  MedicalDocumentPaginated,
} from "@/types/medical-document";

interface MedicalDocumentState {
  documents: MedicalDocument[];
  total: number;
  isLoading: boolean;
  error: string | null;

  fetchDocuments: (
    token: string,
    params?: {
      customer_id?: string;
      booking_id?: string;
      document_type?: string;
      limit?: number;
      offset?: number;
    },
  ) => Promise<void>;
  generateChartDraft: (
    token: string,
    conversationId: string,
  ) => Promise<MedicalDocument>;
  generateConsentForm: (
    token: string,
    bookingId: string,
    language?: string,
  ) => Promise<MedicalDocument>;
  updateStatus: (
    token: string,
    documentId: string,
    status: string,
  ) => Promise<void>;
  deleteDocument: (token: string, documentId: string) => Promise<void>;
}

export const useMedicalDocumentStore = create<MedicalDocumentState>(
  (set) => ({
    documents: [],
    total: 0,
    isLoading: false,
    error: null,

    fetchDocuments: async (token, params = {}) => {
      set({ isLoading: true, error: null });
      try {
        const qs = new URLSearchParams();
        if (params.customer_id) qs.set("customer_id", params.customer_id);
        if (params.booking_id) qs.set("booking_id", params.booking_id);
        if (params.document_type) qs.set("document_type", params.document_type);
        if (params.limit) qs.set("limit", String(params.limit));
        if (params.offset) qs.set("offset", String(params.offset));
        const query = qs.toString() ? `?${qs.toString()}` : "";
        const data = await api.get<MedicalDocumentPaginated>(
          `/api/v1/medical-documents/${query}`,
          { token },
        );
        set({
          documents: data.items,
          total: data.total,
          isLoading: false,
        });
      } catch {
        set({ isLoading: false, error: "Failed to load documents" });
      }
    },

    generateChartDraft: async (token, conversationId) => {
      const doc = await api.post<MedicalDocument>(
        "/api/v1/medical-documents/generate/chart-draft",
        { token, body: { conversation_id: conversationId } },
      );
      set((s) => ({ documents: [doc, ...s.documents], total: s.total + 1 }));
      return doc;
    },

    generateConsentForm: async (token, bookingId, language = "ko") => {
      const doc = await api.post<MedicalDocument>(
        "/api/v1/medical-documents/generate/consent-form",
        { token, body: { booking_id: bookingId, language } },
      );
      set((s) => ({ documents: [doc, ...s.documents], total: s.total + 1 }));
      return doc;
    },

    updateStatus: async (token, documentId, status) => {
      const updated = await api.patch<MedicalDocument>(
        `/api/v1/medical-documents/${documentId}/status`,
        { token, body: { status } },
      );
      set((s) => ({
        documents: s.documents.map((d) =>
          d.id === documentId ? updated : d,
        ),
      }));
    },

    deleteDocument: async (token, documentId) => {
      await api.delete(`/api/v1/medical-documents/${documentId}`, { token });
      set((s) => ({
        documents: s.documents.filter((d) => d.id !== documentId),
        total: s.total - 1,
      }));
    },
  }),
);
