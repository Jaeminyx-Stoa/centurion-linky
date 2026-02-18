"use client";

import { ConversationList } from "@/components/dashboard/conversation-list";
import { ChatWindow } from "@/components/dashboard/chat-window";
import { CustomerPanel } from "@/components/dashboard/customer-panel";
import { useWebSocket } from "@/hooks/use-websocket";

export default function InboxPage() {
  useWebSocket();

  return (
    <>
      <ConversationList />
      <ChatWindow />
      <CustomerPanel />
    </>
  );
}
