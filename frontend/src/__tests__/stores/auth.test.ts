import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/stores/auth";

const mockGet = vi.fn();
const mockPost = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string) {
      super(message);
    }
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      error: null,
    });
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("login", () => {
    it("stores tokens on successful login", async () => {
      mockPost.mockResolvedValueOnce({
        access_token: "access-123",
        refresh_token: "refresh-456",
      });
      mockGet.mockResolvedValueOnce({
        id: "user-1",
        email: "test@clinic.com",
        name: "Admin",
        role: "admin",
        clinic_id: "clinic-1",
      });

      await useAuthStore.getState().login({
        email: "test@clinic.com",
        password: "password",
      });

      expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/login", {
        email: "test@clinic.com",
        password: "password",
      });
      expect(useAuthStore.getState().accessToken).toBe("access-123");
      expect(useAuthStore.getState().refreshToken).toBe("refresh-456");
      expect(useAuthStore.getState().user?.email).toBe("test@clinic.com");
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it("sets error on login failure", async () => {
      mockPost.mockRejectedValueOnce(new Error("Invalid credentials"));

      await useAuthStore.getState().login({
        email: "wrong@test.com",
        password: "wrong",
      });

      expect(useAuthStore.getState().error).toBe("Login failed");
      expect(useAuthStore.getState().accessToken).toBeNull();
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe("logout", () => {
    it("clears all auth state", () => {
      useAuthStore.setState({
        user: { id: "u1", email: "a@b.com", name: "A", role: "admin", clinic_id: "c1", is_active: true },
        accessToken: "token",
        refreshToken: "refresh",
      });
      localStorageMock.setItem("access_token", "token");
      localStorageMock.setItem("refresh_token", "refresh");

      useAuthStore.getState().logout();

      expect(useAuthStore.getState().user).toBeNull();
      expect(useAuthStore.getState().accessToken).toBeNull();
      expect(useAuthStore.getState().refreshToken).toBeNull();
      expect(localStorageMock.getItem("access_token")).toBeNull();
      expect(localStorageMock.getItem("refresh_token")).toBeNull();
    });
  });

  describe("fetchMe", () => {
    it("fetches user profile with token", async () => {
      useAuthStore.setState({ accessToken: "test-token" });
      mockGet.mockResolvedValueOnce({
        id: "user-1",
        email: "test@clinic.com",
        name: "Admin",
        role: "admin",
        clinic_id: "clinic-1",
      });

      await useAuthStore.getState().fetchMe();

      expect(mockGet).toHaveBeenCalledWith("/api/v1/auth/me", { token: "test-token" });
      expect(useAuthStore.getState().user?.name).toBe("Admin");
    });

    it("logs out on fetchMe failure", async () => {
      useAuthStore.setState({ accessToken: "expired-token" });
      mockGet.mockRejectedValueOnce(new Error("Unauthorized"));

      await useAuthStore.getState().fetchMe();

      expect(useAuthStore.getState().accessToken).toBeNull();
      expect(useAuthStore.getState().user).toBeNull();
    });

    it("skips if no token", async () => {
      await useAuthStore.getState().fetchMe();
      expect(mockGet).not.toHaveBeenCalled();
    });
  });

  describe("clearError", () => {
    it("clears error state", () => {
      useAuthStore.setState({ error: "some error" });
      useAuthStore.getState().clearError();
      expect(useAuthStore.getState().error).toBeNull();
    });
  });
});
