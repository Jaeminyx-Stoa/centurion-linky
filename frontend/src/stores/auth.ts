import { create } from "zustand";

import { api, ApiError } from "@/lib/api";
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/auth";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;

  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: typeof window !== "undefined" ? localStorage.getItem("access_token") : null,
  refreshToken: typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null,
  isLoading: false,
  error: null,

  login: async (data: LoginRequest) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await api.post<TokenResponse>("/api/v1/auth/login", data);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isLoading: false,
      });
      await get().fetchMe();
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Login failed";
      set({ isLoading: false, error: message });
    }
  },

  register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await api.post<TokenResponse>("/api/v1/auth/register", data);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isLoading: false,
      });
      await get().fetchMe();
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Registration failed";
      set({ isLoading: false, error: message });
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, accessToken: null, refreshToken: null });
  },

  fetchMe: async () => {
    const token = get().accessToken;
    if (!token) return;
    try {
      const user = await api.get<User>("/api/v1/auth/me", { token });
      set({ user });
    } catch {
      get().logout();
    }
  },

  clearError: () => set({ error: null }),
}));
