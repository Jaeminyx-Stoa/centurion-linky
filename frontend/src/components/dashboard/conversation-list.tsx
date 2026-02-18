"use client";

import { useEffect } from "react";
import { MessageSquare } from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useConversationStore } from "@/stores/conversation";

const COUNTRY_FLAGS: Record<string, string> = {
  JP: "\uD83C\uDDEF\uD83C\uDDF5",
  CN: "\uD83C\uDDE8\uD83C\uDDF3",
  TW: "\uD83C\uDDF9\uD83C\uDDFC",
  US: "\uD83C\uDDFA\uD83C\uDDF8",
  VN: "\uD83C\uDDFB\uD83C\uDDF3",
  TH: "\uD83C\uDDF9\uD83C\uDDED",
  ID: "\uD83C\uDDEE\uD83C\uDDE9",
  KR: "\uD83C\uDDF0\uD83C\uDDF7",
};

const SATISFACTION_COLORS: Record<string, string> = {
  green: "bg-green-500",
  yellow: "bg-yellow-500",
  orange: "bg-orange-500",
  red: "bg-red-500",
};

const MESSENGER_LABELS: Record<string, string> = {
  telegram: "TG",
  line: "LINE",
  instagram: "IG",
  facebook: "FB",
  whatsapp: "WA",
  kakao: "KT",
};

export function ConversationList() {
  const { accessToken } = useAuthStore();
  const {
    conversations,
    selectedId,
    fetchConversations,
    selectConversation,
  } = useConversationStore();

  useEffect(() => {
    if (accessToken) {
      fetchConversations(accessToken);
    }
  }, [accessToken, fetchConversations]);

  const handleSelect = (id: string) => {
    if (accessToken) {
      selectConversation(accessToken, id);
    }
  };

  return (
    <div className="flex w-[280px] flex-col border-r">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <h2 className="text-sm font-semibold">받은 메시지</h2>
        <p className="text-xs text-muted-foreground">
          {conversations.length}개 대화
        </p>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
            <MessageSquare className="mb-2 h-8 w-8" />
            <p className="text-sm">대화가 없습니다</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => handleSelect(conv.id)}
              className={`flex w-full items-start gap-3 border-b px-4 py-3 text-left transition-colors ${
                selectedId === conv.id
                  ? "bg-muted"
                  : "hover:bg-muted/50"
              }`}
            >
              {/* Country flag */}
              <div className="flex flex-col items-center gap-1 pt-0.5">
                <span className="text-lg">
                  {COUNTRY_FLAGS[conv.customer_country || ""] || "\uD83C\uDF10"}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  {MESSENGER_LABELS[conv.messenger_type || ""] || ""}
                </span>
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">
                    {conv.customer_name || "알 수 없음"}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {conv.satisfaction_level && (
                      <div
                        className={`h-2 w-2 rounded-full ${
                          SATISFACTION_COLORS[conv.satisfaction_level] || ""
                        }`}
                      />
                    )}
                    {conv.unread_count > 0 && (
                      <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] text-primary-foreground">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {conv.last_message_preview || "..."}
                </p>
                <div className="mt-1 flex items-center gap-2">
                  {!conv.ai_mode && (
                    <span className="rounded bg-orange-100 px-1 text-[10px] text-orange-700">
                      수동
                    </span>
                  )}
                  {conv.status === "resolved" && (
                    <span className="rounded bg-green-100 px-1 text-[10px] text-green-700">
                      해결
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
