import { describe, expect, it, beforeEach } from "vitest";
import { act } from "@testing-library/react";

import { useNotificationStore } from "@/stores/notification";

describe("notification store", () => {
  beforeEach(() => {
    // Reset store state
    useNotificationStore.setState({
      notifications: [],
      unreadCount: 0,
    });
  });

  it("adds a notification and increments unread count", () => {
    act(() => {
      useNotificationStore.getState().addNotification({
        type: "escalation",
        title: "Test",
        message: "Test message",
      });
    });

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(1);
    expect(state.unreadCount).toBe(1);
    expect(state.notifications[0].read).toBe(false);
    expect(state.notifications[0].type).toBe("escalation");
  });

  it("marks all notifications as read", () => {
    act(() => {
      const store = useNotificationStore.getState();
      store.addNotification({ type: "escalation", title: "A", message: "a" });
      store.addNotification({ type: "quota_warning", title: "B", message: "b" });
    });

    expect(useNotificationStore.getState().unreadCount).toBe(2);

    act(() => {
      useNotificationStore.getState().markAllRead();
    });

    const state = useNotificationStore.getState();
    expect(state.unreadCount).toBe(0);
    expect(state.notifications.every((n) => n.read)).toBe(true);
  });

  it("dismisses a notification by id", () => {
    act(() => {
      const store = useNotificationStore.getState();
      store.addNotification({ type: "escalation", title: "A", message: "a" });
      store.addNotification({ type: "delivery_failed", title: "B", message: "b" });
    });

    const firstId = useNotificationStore.getState().notifications[0].id;

    act(() => {
      useNotificationStore.getState().dismiss(firstId);
    });

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0].id).not.toBe(firstId);
  });

  it("limits to 50 notifications", () => {
    act(() => {
      const store = useNotificationStore.getState();
      for (let i = 0; i < 60; i++) {
        store.addNotification({
          type: "escalation",
          title: `Notification ${i}`,
          message: `Message ${i}`,
        });
      }
    });

    expect(useNotificationStore.getState().notifications).toHaveLength(50);
  });

  it("newest notifications appear first", () => {
    act(() => {
      const store = useNotificationStore.getState();
      store.addNotification({ type: "escalation", title: "First", message: "1" });
      store.addNotification({ type: "quota_warning", title: "Second", message: "2" });
    });

    const state = useNotificationStore.getState();
    expect(state.notifications[0].title).toBe("Second");
    expect(state.notifications[1].title).toBe("First");
  });
});
