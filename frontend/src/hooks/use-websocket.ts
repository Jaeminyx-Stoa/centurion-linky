"use client";

import { useEffect, useRef } from "react";

import { useAuthStore } from "@/stores/auth";
import { useConversationStore } from "@/stores/conversation";
import type { Message } from "@/types/conversation";

const WS_BASE_URL =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    .replace("http://", "ws://")
    .replace("https://", "wss://");

export function useWebSocket() {
  const { accessToken } = useAuthStore();
  const { onNewMessage, onConversationUpdate } = useConversationStore();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    const ws = new WebSocket(`${WS_BASE_URL}/ws?token=${accessToken}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "connected":
            break;
          case "new_message":
            if (data.message) {
              onNewMessage(data.message as Message);
            }
            break;
          case "conversation_update":
            if (data.conversation) {
              onConversationUpdate(data.conversation);
            }
            break;
          case "escalation_alert":
            // Could show a toast notification
            break;
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onclose = () => {
      // Auto-reconnect after 3s
      setTimeout(() => {
        if (wsRef.current === ws) {
          wsRef.current = null;
        }
      }, 3000);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [accessToken, onNewMessage, onConversationUpdate]);
}
