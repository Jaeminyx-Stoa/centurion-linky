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
  FlaskConical,
  Settings,
  LogOut,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "대시보드", href: "/" },
  { icon: MessageSquare, label: "받은 메시지", href: "/conversations" },
  { icon: Users, label: "고객", href: "/customers" },
  { icon: Calendar, label: "예약", href: "/bookings" },
  { icon: CreditCard, label: "결제", href: "/payments" },
  { icon: Syringe, label: "시술", href: "/procedures" },
  { icon: Heart, label: "CRM", href: "/crm" },
  { icon: BarChart3, label: "통계", href: "/analytics" },
  { icon: BookOpen, label: "지식 관리", href: "/knowledge" },
  { icon: FlaskConical, label: "AI Lab", href: "/ai-lab" },
  { icon: Settings, label: "설정", href: "/settings" },
];

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="flex w-[60px] flex-col items-center border-r bg-muted/30 py-4">
      <div className="mb-6 text-lg font-bold text-primary">M</div>
      <nav className="flex flex-1 flex-col items-center gap-2">
        {NAV_ITEMS.map(({ icon: Icon, label, href }) => {
          const isActive = pathname === href;
          return (
            <button
              key={href}
              onClick={() => router.push(href)}
              className={`flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
              title={label}
            >
              <Icon className="h-5 w-5" />
            </button>
          );
        })}
      </nav>
      <button
        onClick={handleLogout}
        className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
        title="로그아웃"
      >
        <LogOut className="h-5 w-5" />
      </button>
    </div>
  );
}
