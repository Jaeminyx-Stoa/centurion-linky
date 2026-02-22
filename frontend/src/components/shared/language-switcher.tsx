"use client";

import { useI18nStore, type Locale } from "@/i18n";

const LOCALE_CYCLE: Locale[] = ["ko", "en", "ja", "zh", "vi"];

const LOCALE_LABELS: Record<Locale, string> = {
  ko: "한국어",
  en: "EN",
  ja: "日本語",
  zh: "中文",
  vi: "Tiếng Việt",
};

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18nStore();

  const handleClick = () => {
    const idx = LOCALE_CYCLE.indexOf(locale);
    const next = LOCALE_CYCLE[(idx + 1) % LOCALE_CYCLE.length];
    setLocale(next);
  };

  const nextLocale = LOCALE_CYCLE[(LOCALE_CYCLE.indexOf(locale) + 1) % LOCALE_CYCLE.length];

  return (
    <button
      onClick={handleClick}
      className="rounded-full border px-2 py-0.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted"
      aria-label={`Switch language to ${LOCALE_LABELS[nextLocale]}`}
    >
      {LOCALE_LABELS[locale]}
    </button>
  );
}
