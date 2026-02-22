import { create } from "zustand";

export interface Notification {
  id: string;
  type: "escalation" | "satisfaction_warning" | "delivery_failed" | "quota_warning" | "quota_exceeded";
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
}

const MAX_NOTIFICATIONS = 50;

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
  markAllRead: () => void;
  dismiss: (id: string) => void;
}

let nextId = 1;

export const useNotificationStore = create<NotificationState>()((set) => ({
  notifications: [],
  unreadCount: 0,

  addNotification: (notification) =>
    set((state) => {
      const newNotification: Notification = {
        ...notification,
        id: String(nextId++),
        timestamp: Date.now(),
        read: false,
      };
      const updated = [newNotification, ...state.notifications].slice(0, MAX_NOTIFICATIONS);
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.read).length,
      };
    }),

  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),

  dismiss: (id) =>
    set((state) => {
      const updated = state.notifications.filter((n) => n.id !== id);
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.read).length,
      };
    }),
}));
