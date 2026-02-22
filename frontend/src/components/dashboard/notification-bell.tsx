"use client";

import { useState, useRef, useEffect } from "react";
import { Bell } from "lucide-react";

import { useNotificationStore } from "@/stores/notification";
import { useT } from "@/i18n";

export function NotificationBell() {
  const { notifications, unreadCount, markAllRead } = useNotificationStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const t = useT();

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute bottom-full left-1/2 mb-2 w-72 -translate-x-1/2 rounded-lg border bg-popover shadow-lg md:bottom-auto md:left-auto md:right-0 md:top-full md:mt-2 md:translate-x-0">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <span className="text-xs font-medium">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-primary hover:underline"
              >
                {t("notification.markAllRead")}
              </button>
            )}
          </div>
          <div className="max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-3 py-6 text-center text-xs text-muted-foreground">
                {t("notification.empty")}
              </p>
            ) : (
              notifications.slice(0, 20).map((n) => (
                <div
                  key={n.id}
                  className={`border-b px-3 py-2 last:border-b-0 ${
                    n.read ? "opacity-60" : ""
                  }`}
                >
                  <p className="text-xs font-medium">{n.title}</p>
                  <p className="text-[11px] text-muted-foreground">{n.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
