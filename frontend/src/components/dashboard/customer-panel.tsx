"use client";

import {
  Globe,
  MessageCircle,
  Calendar,
  Tag,
  FileText,
} from "lucide-react";

import { useConversationStore } from "@/stores/conversation";

const COUNTRY_FLAGS: Record<string, string> = {
  JP: "\uD83C\uDDEF\uD83C\uDDF5",
  CN: "\uD83C\uDDE8\uD83C\uDDF3",
  TW: "\uD83C\uDDF9\uD83C\uDDFC",
  US: "\uD83C\uDDFA\uD83C\uDDF8",
  VN: "\uD83C\uDDFB\uD83C\uDDF3",
  TH: "\uD83C\uDDF9\uD83C\uDDED",
  ID: "\uD83C\uDDEE\uD83C\uDDE9",
};

const LANGUAGE_NAMES: Record<string, string> = {
  ja: "\uC77C\uBCF8\uC5B4",
  en: "\uC601\uC5B4",
  "zh-CN": "\uC911\uAD6D\uC5B4(\uAC04\uCCB4)",
  "zh-TW": "\uC911\uAD6D\uC5B4(\uBC88\uCCB4)",
  vi: "\uBCA0\uD2B8\uB0A8\uC5B4",
  th: "\uD0DC\uAD6D\uC5B4",
  id: "\uC778\uB3C4\uB124\uC2DC\uC544\uC5B4",
  ko: "\uD55C\uAD6D\uC5B4",
};

export function CustomerPanel() {
  const { customer, selectedDetail } = useConversationStore();

  if (!customer || !selectedDetail) {
    return (
      <div className="flex w-[320px] items-center justify-center border-l text-sm text-muted-foreground">
        고객 정보 없음
      </div>
    );
  }

  return (
    <div className="flex w-[320px] flex-col border-l overflow-y-auto">
      {/* Profile */}
      <div className="border-b p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-lg">
            {COUNTRY_FLAGS[customer.country_code || ""] || "\uD83D\uDC64"}
          </div>
          <div>
            <p className="font-medium">
              {customer.display_name || customer.name || "\uC54C \uC218 \uC5C6\uC74C"}
            </p>
            <p className="text-xs text-muted-foreground">
              {customer.messenger_type} &middot; {customer.messenger_user_id}
            </p>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="border-b p-4 space-y-3">
        <h3 className="text-xs font-semibold uppercase text-muted-foreground">
          고객 정보
        </h3>

        <div className="flex items-center gap-2 text-sm">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <span>
            {customer.country_code || "-"}{" "}
            {customer.language_code
              ? `(${LANGUAGE_NAMES[customer.language_code] || customer.language_code})`
              : ""}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <MessageCircle className="h-4 w-4 text-muted-foreground" />
          <span>{customer.messenger_type}</span>
        </div>

        {customer.phone && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">\uD83D\uDCDE</span>
            <span>{customer.phone}</span>
          </div>
        )}

        {customer.email && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">\u2709\uFE0F</span>
            <span>{customer.email}</span>
          </div>
        )}

        <div className="flex items-center gap-2 text-sm">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span>
            예약 {customer.total_bookings}건
            {customer.last_visit_at && (
              <> &middot; 마지막 {new Date(customer.last_visit_at).toLocaleDateString("ko")}</>
            )}
          </span>
        </div>
      </div>

      {/* Satisfaction */}
      {selectedDetail.satisfaction_score !== null && (
        <div className="border-b p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
            만족도
          </h3>
          <div className="flex items-center gap-2">
            <div
              className={`h-3 w-3 rounded-full ${
                {
                  green: "bg-green-500",
                  yellow: "bg-yellow-500",
                  orange: "bg-orange-500",
                  red: "bg-red-500",
                }[selectedDetail.satisfaction_level || ""] || "bg-gray-300"
              }`}
            />
            <span className="text-lg font-bold">
              {selectedDetail.satisfaction_score}
            </span>
            <span className="text-sm text-muted-foreground">/ 100</span>
          </div>
        </div>
      )}

      {/* Tags */}
      {customer.tags && customer.tags.length > 0 && (
        <div className="border-b p-4">
          <h3 className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase text-muted-foreground">
            <Tag className="h-3 w-3" /> 태그
          </h3>
          <div className="flex flex-wrap gap-1">
            {customer.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-muted px-2 py-0.5 text-xs"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {customer.notes && (
        <div className="p-4">
          <h3 className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase text-muted-foreground">
            <FileText className="h-3 w-3" /> 메모
          </h3>
          <p className="text-sm whitespace-pre-wrap">{customer.notes}</p>
        </div>
      )}
    </div>
  );
}
