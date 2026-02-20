"use client";

import { useCallback, useEffect, useRef } from "react";

import { useAuthStore } from "@/stores/auth";
import { useConversationStore } from "@/stores/conversation";
import type { Message } from "@/types/conversation";

const WS_BASE_URL =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    .replace("http://", "ws://")
    .replace("https://", "wss://");

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 3000;
const MAX_DELAY_MS = 30000;

export function useWebSocket() {
  const { accessToken } = useAuthStore();
  const { onNewMessage, onConversationUpdate } = useConversationStore();
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!accessToken) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE_URL}/ws?token=${accessToken}`);
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
    };

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

    ws.onerror = () => {
      // Error is followed by close event; reconnect logic lives there
    };

    ws.onclose = () => {
      wsRef.current = null;

      if (retriesRef.current < MAX_RETRIES) {
        const delay = Math.min(
          BASE_DELAY_MS * Math.pow(2, retriesRef.current),
          MAX_DELAY_MS,
        );
        retriesRef.current += 1;
        reconnectTimerRef.current = setTimeout(connect, delay);
      }
    };
  }, [accessToken, onNewMessage, onConversationUpdate]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      retriesRef.current = MAX_RETRIES; // prevent reconnect during cleanup
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);
}
