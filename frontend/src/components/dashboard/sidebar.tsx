"use client";

import { useRouter, usePathname } from "next/navigation";
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
  FileText,
  FlaskConical,
  DollarSign,
  Camera,
  Languages,
  Settings,
  LogOut,
  Menu,
  X,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useUIStore } from "@/stores/ui";
import { useT, type TranslationKey } from "@/i18n";
import { LanguageSwitcher } from "@/components/shared/language-switcher";
import { NotificationBell } from "@/components/dashboard/notification-bell";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

const NAV_ITEMS: { icon: React.ElementType; labelKey: TranslationKey; href: string }[] = [
  { icon: LayoutDashboard, labelKey: "nav.dashboard", href: "/" },
  { icon: MessageSquare, labelKey: "nav.conversations", href: "/conversations" },
  { icon: Users, labelKey: "nav.customers", href: "/customers" },
  { icon: Calendar, labelKey: "nav.bookings", href: "/bookings" },
  { icon: CreditCard, labelKey: "nav.payments", href: "/payments" },
  { icon: Syringe, labelKey: "nav.procedures", href: "/procedures" },
  { icon: Heart, labelKey: "nav.crm", href: "/crm" },
  { icon: BarChart3, labelKey: "nav.analytics", href: "/analytics" },
  { icon: FileText, labelKey: "nav.documents", href: "/documents" },
  { icon: Camera, labelKey: "nav.photos", href: "/treatment-photos" },
  { icon: BookOpen, labelKey: "nav.knowledge", href: "/knowledge" },
  { icon: Languages, labelKey: "nav.translationQA", href: "/translation-qa" },
  { icon: FlaskConical, labelKey: "nav.aiLab", href: "/ai-lab" },
  { icon: DollarSign, labelKey: "llmUsage.title", href: "/llm-usage" },
  { icon: Settings, labelKey: "nav.settings", href: "/settings" },
];

function NavItems({ expanded, onNavigate }: { expanded: boolean; onNavigate?: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const t = useT();

  return (
    <>
      {NAV_ITEMS.map(({ icon: Icon, labelKey, href }) => {
        const label = t(labelKey);
        const isActive = pathname === href;
        return (
          <button
            key={href}
            onClick={() => {
              router.push(href);
              onNavigate?.();
            }}
            aria-label={label}
            aria-current={isActive ? "page" : undefined}
            className={`flex items-center gap-3 rounded-lg transition-colors ${
              expanded ? "w-full px-3 py-2" : "h-10 w-10 justify-center"
            } ${
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <Icon className="h-5 w-5 shrink-0" />
            {expanded && <span className="text-sm">{label}</span>}
            {!expanded && <span className="sr-only">{label}</span>}
          </button>
        );
      })}
    </>
  );
}

/** Desktop sidebar: icon-only (60px) */
export function Sidebar() {
  const { logout } = useAuthStore();
  const router = useRouter();
  const t = useT();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="hidden md:flex w-[60px] flex-col items-center border-r bg-muted/30 py-4">
      <div className="mb-6 text-lg font-bold text-primary">M</div>
      <nav className="flex flex-1 flex-col items-center gap-2" aria-label={t("nav.mainNav")}>
        <NavItems expanded={false} />
      </nav>
      <div className="mb-2 flex flex-col items-center gap-2">
        <NotificationBell />
        <ThemeToggle />
        <LanguageSwitcher />
      </div>
      <button
        onClick={handleLogout}
        aria-label={t("nav.logout")}
        className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
      >
        <LogOut className="h-5 w-5" />
        <span className="sr-only">{t("nav.logout")}</span>
      </button>
    </div>
  );
}

/** Mobile top header bar with hamburger menu */
export function MobileHeader() {
  const { mobileMenuOpen, setMobileMenuOpen } = useUIStore();
  const { logout } = useAuthStore();
  const router = useRouter();
  const t = useT();

  const handleLogout = () => {
    logout();
    setMobileMenuOpen(false);
    router.push("/login");
  };

  return (
    <>
      {/* Top bar */}
      <div className="flex md:hidden items-center justify-between border-b px-4 py-2">
        <button
          onClick={() => setMobileMenuOpen(true)}
          aria-label={t("nav.openMenu")}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="text-sm font-bold text-primary">Linky</span>
        <div className="flex items-center gap-2">
          <NotificationBell />
          <ThemeToggle />
          <LanguageSwitcher />
        </div>
      </div>

      {/* Mobile drawer */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="p-0">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <SheetTitle className="text-base">Linky</SheetTitle>
            <button
              onClick={() => setMobileMenuOpen(false)}
              aria-label={t("nav.closeMenu")}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <SheetDescription className="sr-only">{t("nav.navMenu")}</SheetDescription>
          <nav className="flex-1 overflow-y-auto p-3 space-y-1" aria-label={t("nav.mainNav")}>
            <NavItems expanded onNavigate={() => setMobileMenuOpen(false)} />
          </nav>
          <div className="border-t p-3">
            <button
              onClick={handleLogout}
              aria-label={t("nav.logout")}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
            >
              <LogOut className="h-5 w-5 shrink-0" />
              {t("nav.logout")}
            </button>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
