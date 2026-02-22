import { create } from "zustand";
import { persist } from "zustand/middleware";

import ko, { type TranslationKey } from "./ko";
import en from "./en";
import ja from "./ja";
import zh from "./zh";
import vi from "./vi";

export type Locale = "ko" | "en" | "ja" | "zh" | "vi";

const TRANSLATIONS: Record<Locale, Record<TranslationKey, string>> = { ko, en, ja, zh, vi };

interface I18nState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const useI18nStore = create<I18nState>()(
  persist(
    (set) => ({
      locale: "ko",
      setLocale: (locale) => set({ locale }),
    }),
    { name: "i18n-locale" },
  ),
);

/**
 * Translation hook.
 *
 * Usage:
 *   const t = useT();
 *   t("nav.dashboard")  // "대시보드" or "Dashboard"
 *   t("pagination.showing", { start: 1, end: 20, total: 100 })
 */
export function useT() {
  const locale = useI18nStore((s) => s.locale);
  const dict = TRANSLATIONS[locale];

  return function t(key: TranslationKey, params?: Record<string, string | number>): string {
    let value = dict[key] ?? key;
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        value = value.replace(`{${k}}`, String(v));
      }
    }
    return value;
  };
}

export type { TranslationKey };
