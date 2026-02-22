import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";

interface UIState {
  sidebarExpanded: boolean;
  mobileMenuOpen: boolean;
  theme: Theme;
  toggleSidebar: () => void;
  setMobileMenuOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarExpanded: false,
      mobileMenuOpen: false,
      theme: "system" as Theme,
      toggleSidebar: () =>
        set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),
      setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "ui-store",
      partialize: (state) => ({ theme: state.theme }),
    },
  ),
);
