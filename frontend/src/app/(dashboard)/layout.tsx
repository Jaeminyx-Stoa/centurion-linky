"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/stores/auth";
import { Sidebar, MobileHeader } from "@/components/dashboard/sidebar";
import { ErrorBoundary } from "@/components/shared/error-boundary";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, accessToken, fetchMe } = useAuthStore();

  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
      return;
    }
    if (!user) {
      fetchMe();
    }
  }, [accessToken, user, fetchMe, router]);

  if (!accessToken) return null;

  return (
    <div className="flex h-screen flex-col md:flex-row overflow-hidden">
      <MobileHeader />
      <Sidebar />
      <main className="flex flex-1 overflow-hidden">
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    </div>
  );
}
