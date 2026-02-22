"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { useNotificationStore, type Notification } from "@/stores/notification";

const BORDER_COLORS: Record<Notification["type"], string> = {
  escalation: "border-l-red-500",
  satisfaction_warning: "border-l-yellow-500",
  delivery_failed: "border-l-red-400",
  quota_warning: "border-l-yellow-500",
  quota_exceeded: "border-l-red-500",
};

export function NotificationToast() {
  const { notifications } = useNotificationStore();
  const [visibleIds, setVisibleIds] = useState<Set<string>>(new Set());

  // Show toast for new notifications, auto-dismiss after 3s
  useEffect(() => {
    if (notifications.length === 0) return;
    const latest = notifications[0];
    if (!latest || visibleIds.has(latest.id)) return;

    setVisibleIds((prev) => new Set(prev).add(latest.id));

    const timer = setTimeout(() => {
      setVisibleIds((prev) => {
        const next = new Set(prev);
        next.delete(latest.id);
        return next;
      });
    }, 3000);

    return () => clearTimeout(timer);
  }, [notifications, visibleIds]);

  const toasts = notifications.filter((n) => visibleIds.has(n.id));

  if (toasts.length === 0) return null;

  return (
    <div className="fixed right-4 top-4 z-[60] flex flex-col gap-2" data-testid="notification-toasts">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`border-l-4 ${BORDER_COLORS[toast.type]} rounded-lg border bg-popover p-3 shadow-lg animate-in slide-in-from-right-full`}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-medium">{toast.title}</p>
              <p className="text-xs text-muted-foreground">{toast.message}</p>
            </div>
            <button
              onClick={() =>
                setVisibleIds((prev) => {
                  const next = new Set(prev);
                  next.delete(toast.id);
                  return next;
                })
              }
              className="shrink-0 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
