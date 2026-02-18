"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Shield } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/auth";
import { useConversationStore } from "@/stores/conversation";

export function ChatWindow() {
  const { accessToken } = useAuthStore();
  const {
    selectedId,
    selectedDetail,
    messages,
    isLoading,
    sendMessage,
    toggleAi,
    resolveConversation,
  } = useConversationStore();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!selectedId || !selectedDetail) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <p>대화를 선택하세요</p>
      </div>
    );
  }

  const handleSend = async () => {
    if (!input.trim() || !accessToken) return;
    await sendMessage(accessToken, selectedId, input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleToggleAi = () => {
    if (accessToken) toggleAi(accessToken, selectedId);
  };

  const handleResolve = () => {
    if (accessToken) resolveConversation(accessToken, selectedId);
  };

  return (
    <div className="flex flex-1 flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {selectedDetail.status === "active" ? "상담 중" : selectedDetail.status}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={selectedDetail.ai_mode ? "default" : "outline"}
            size="sm"
            onClick={handleToggleAi}
            className="gap-1"
          >
            {selectedDetail.ai_mode ? (
              <>
                <Bot className="h-3.5 w-3.5" /> AI 모드
              </>
            ) : (
              <>
                <User className="h-3.5 w-3.5" /> 수동 모드
              </>
            )}
          </Button>
          {selectedDetail.status !== "resolved" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleResolve}
              className="gap-1"
            >
              <Shield className="h-3.5 w-3.5" /> 해결
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            로딩 중...
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender_type === "customer" ? "justify-start" : "justify-end"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-3 py-2 ${
                  msg.sender_type === "customer"
                    ? "bg-muted"
                    : msg.sender_type === "ai"
                      ? "bg-primary/10 text-foreground"
                      : "bg-blue-100 text-foreground"
                }`}
              >
                {/* Sender label */}
                <div className="mb-0.5 flex items-center gap-1">
                  {msg.sender_type === "customer" && (
                    <span className="text-[10px] text-muted-foreground">고객</span>
                  )}
                  {msg.sender_type === "ai" && (
                    <span className="text-[10px] text-primary">
                      <Bot className="inline h-3 w-3" /> AI
                    </span>
                  )}
                  {msg.sender_type === "staff" && (
                    <span className="text-[10px] text-blue-600">
                      <User className="inline h-3 w-3" /> 상담사
                    </span>
                  )}
                </div>

                {/* Content */}
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                {/* Translation (for customer messages) */}
                {msg.translated_content && msg.sender_type === "customer" && (
                  <p className="mt-1 border-t border-border/50 pt-1 text-xs text-muted-foreground">
                    {msg.translated_content}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지 입력..."
            disabled={selectedDetail.status === "resolved"}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || selectedDetail.status === "resolved"}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
