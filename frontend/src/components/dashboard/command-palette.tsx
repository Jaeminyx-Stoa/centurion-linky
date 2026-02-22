"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  Calendar,
  CreditCard,
  Syringe,
  Heart,
  BarChart3,
  BookOpen,
  FlaskConical,
  DollarSign,
  Settings,
} from "lucide-react";

import { useT, type TranslationKey } from "@/i18n";

const NAV_ITEMS: { icon: React.ElementType; labelKey: TranslationKey; href: string }[] = [
  { icon: LayoutDashboard, labelKey: "nav.dashboard", href: "/" },
  { icon: MessageSquare, labelKey: "nav.conversations", href: "/conversations" },
  { icon: Users, labelKey: "nav.customers", href: "/customers" },
  { icon: Calendar, labelKey: "nav.bookings", href: "/bookings" },
  { icon: CreditCard, labelKey: "nav.payments", href: "/payments" },
  { icon: Syringe, labelKey: "nav.procedures", href: "/procedures" },
  { icon: Heart, labelKey: "nav.crm", href: "/crm" },
  { icon: BarChart3, labelKey: "nav.analytics", href: "/analytics" },
  { icon: BookOpen, labelKey: "nav.knowledge", href: "/knowledge" },
  { icon: FlaskConical, labelKey: "nav.aiLab", href: "/ai-lab" },
  { icon: DollarSign, labelKey: "llmUsage.title", href: "/llm-usage" },
  { icon: Settings, labelKey: "nav.settings", href: "/settings" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const t = useT();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSelect = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50" data-testid="command-palette">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={() => setOpen(false)}
      />

      {/* Command dialog */}
      <div className="absolute left-1/2 top-[20%] w-full max-w-lg -translate-x-1/2">
        <Command
          className="rounded-lg border bg-popover text-popover-foreground shadow-lg"
          label={t("command.title")}
        >
          <Command.Input
            placeholder={t("command.placeholder")}
            className="w-full border-b bg-transparent px-4 py-3 text-sm outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-[300px] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              {t("command.noResults")}
            </Command.Empty>

            <Command.Group
              heading={t("command.navigation")}
              className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground"
            >
              {NAV_ITEMS.map(({ icon: Icon, labelKey, href }) => (
                <Command.Item
                  key={href}
                  value={t(labelKey)}
                  onSelect={() => handleSelect(href)}
                  className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 text-sm aria-selected:bg-accent aria-selected:text-accent-foreground"
                >
                  <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  {t(labelKey)}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
