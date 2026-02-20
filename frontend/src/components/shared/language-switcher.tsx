"use client";

import { useI18nStore, type Locale } from "@/i18n";

const LOCALE_LABELS: Record<Locale, string> = {
  ko: "한국어",
  en: "EN",
};

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18nStore();

  return (
    <button
      onClick={() => setLocale(locale === "ko" ? "en" : "ko")}
      className="rounded-full border px-2 py-0.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted"
      aria-label={`Switch language to ${locale === "ko" ? "English" : "한국어"}`}
    >
      {LOCALE_LABELS[locale]}
    </button>
  );
}
