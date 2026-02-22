"use client";

import { Sun, Moon, Monitor } from "lucide-react";
import { useUIStore, type Theme } from "@/stores/ui";
import { useT, type TranslationKey } from "@/i18n";

const CYCLE: Theme[] = ["light", "dark", "system"];

const ICONS: Record<Theme, React.ElementType> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};

const LABEL_KEYS: Record<Theme, TranslationKey> = {
  light: "theme.light",
  dark: "theme.dark",
  system: "theme.system",
};

export function ThemeToggle() {
  const { theme, setTheme } = useUIStore();
  const t = useT();

  const next = () => {
    const idx = CYCLE.indexOf(theme);
    setTheme(CYCLE[(idx + 1) % CYCLE.length]);
  };

  const Icon = ICONS[theme];

  return (
    <button
      onClick={next}
      className="rounded-full border px-2 py-0.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted"
      aria-label={t(LABEL_KEYS[theme])}
    >
      <Icon className="h-3.5 w-3.5" />
    </button>
  );
}
