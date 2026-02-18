"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/dashboard/sidebar";

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
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
