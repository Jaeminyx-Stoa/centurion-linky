"use client";

import { useEffect, useState } from "react";
import {
  Heart,
  Calendar,
  AlertCircle,
  XCircle,
  ClipboardList,
  Star,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useCRMStore } from "@/stores/crm";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ListSkeleton } from "@/components/shared/skeletons";
import { PaginationControls } from "@/components/shared/pagination-controls";

type TabId = "events" | "surveys";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "events", label: "CRM 이벤트", icon: Calendar },
  { id: "surveys", label: "만족도 설문", icon: ClipboardList },
];

const EVENT_STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-50 text-blue-700",
  sent: "bg-yellow-50 text-yellow-700",
  completed: "bg-green-50 text-green-700",
  cancelled: "bg-gray-100 text-gray-500",
  failed: "bg-red-50 text-red-700",
};

function EventsTab() {
  const { accessToken } = useAuthStore();
  const {
    events, eventsPage, eventsPageSize, eventsTotal,
    cancelEvent, setEventsPage,
  } = useCRMStore();
  const [statusFilter, setStatusFilter] = useState("all");

  const STATUS_FILTERS = [
    { id: "all", label: "전체" },
    { id: "scheduled", label: "예정" },
    { id: "sent", label: "발송" },
    { id: "completed", label: "완료" },
    { id: "cancelled", label: "취소" },
    { id: "failed", label: "실패" },
  ];

  useEffect(() => {
    if (accessToken) {
      useCRMStore
        .getState()
        .fetchEvents(
          accessToken,
          statusFilter === "all" ? undefined : statusFilter,
        );
    }
  }, [accessToken, statusFilter, eventsPage]);

  const handleCancel = async (id: string) => {
    if (!accessToken) return;
    await cancelEvent(accessToken, id);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2 overflow-x-auto">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => { setStatusFilter(f.id); setEventsPage(1); }}
            aria-pressed={statusFilter === f.id}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs transition-colors ${
              statusFilter === f.id
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {events.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
          <Calendar className="mb-2 h-8 w-8" />
          <p className="text-sm">CRM 이벤트가 없습니다</p>
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {events.map((event) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                >
                  <div>
                    <p className="text-sm font-medium">{event.event_type}</p>
                    <p className="text-xs text-muted-foreground">
                      예정:{" "}
                      {new Date(event.scheduled_at).toLocaleString("ko-KR")}
                      {event.executed_at &&
                        ` | 실행: ${new Date(event.executed_at).toLocaleString("ko-KR")}`}
                    </p>
                    {event.message_content && (
                      <p className="mt-1 truncate text-xs text-muted-foreground max-w-md">
                        {event.message_content}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        EVENT_STATUS_COLORS[event.status] ||
                        "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {event.status}
                    </span>
                    {event.status === "scheduled" && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs text-destructive hover:text-destructive"
                        onClick={() => handleCancel(event.id)}
                        aria-label="이벤트 취소"
                      >
                        <XCircle className="mr-1 h-3 w-3" />
                        취소
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <PaginationControls
              page={eventsPage}
              pageSize={eventsPageSize}
              total={eventsTotal}
              onPageChange={setEventsPage}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SurveysTab() {
  const { surveys, surveySummary, surveysPage, surveysPageSize, surveysTotal, setSurveysPage } = useCRMStore();
  const { accessToken } = useAuthStore();
  const [roundFilter, setRoundFilter] = useState<number | null>(null);

  useEffect(() => {
    if (accessToken) {
      useCRMStore
        .getState()
        .fetchSurveys(accessToken, roundFilter || undefined);
    }
  }, [accessToken, roundFilter, surveysPage]);

  return (
    <div className="space-y-4">
      {/* Summary */}
      {surveySummary && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <Card>
            <CardContent className="pt-0">
              <p className="text-sm text-muted-foreground">총 설문</p>
              <p className="text-2xl font-bold">
                {surveySummary.total_surveys}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-0">
              <p className="text-sm text-muted-foreground">평균 종합</p>
              <p className="text-2xl font-bold">
                {surveySummary.avg_overall?.toFixed(1) || "-"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-0">
              <p className="text-sm text-muted-foreground">서비스</p>
              <p className="text-2xl font-bold">
                {surveySummary.avg_service?.toFixed(1) || "-"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-0">
              <p className="text-sm text-muted-foreground">결과</p>
              <p className="text-2xl font-bold">
                {surveySummary.avg_result?.toFixed(1) || "-"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-0">
              <p className="text-sm text-muted-foreground">NPS</p>
              <p className="text-2xl font-bold">
                {surveySummary.avg_nps?.toFixed(1) || "-"}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Round Filter */}
      <div className="flex gap-2 overflow-x-auto">
        {[null, 1, 2, 3].map((r) => (
          <button
            key={r ?? "all"}
            onClick={() => { setRoundFilter(r); setSurveysPage(1); }}
            aria-pressed={roundFilter === r}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs transition-colors ${
              roundFilter === r
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80"
            }`}
          >
            {r === null ? "전체" : `${r}차`}
          </button>
        ))}
      </div>

      {/* Survey List */}
      {surveys.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
          <ClipboardList className="mb-2 h-8 w-8" />
          <p className="text-sm">설문 데이터가 없습니다</p>
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {surveys.map((survey) => (
                <div
                  key={survey.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {survey.survey_round}차 설문
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(survey.created_at).toLocaleDateString("ko-KR")}
                      {survey.would_revisit &&
                        ` | 재방문: ${survey.would_revisit}`}
                    </p>
                    {survey.feedback_text && (
                      <p className="mt-1 truncate text-xs text-muted-foreground max-w-lg">
                        {survey.feedback_text}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 text-sm">
                      <Star className="h-3.5 w-3.5 text-yellow-500" />
                      <span className="font-medium">
                        {survey.overall_score}
                      </span>
                    </div>
                    {survey.nps_score != null && (
                      <span className="text-xs text-muted-foreground">
                        NPS: {survey.nps_score}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <PaginationControls
              page={surveysPage}
              pageSize={surveysPageSize}
              total={surveysTotal}
              onPageChange={setSurveysPage}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function CRMPage() {
  const { accessToken } = useAuthStore();
  const { isLoading, error, fetchAll } = useCRMStore();
  const [activeTab, setActiveTab] = useState<TabId>("events");

  useEffect(() => {
    if (accessToken) {
      fetchAll(accessToken);
    }
  }, [accessToken, fetchAll]);

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
        <div className="hidden md:flex w-[180px] flex-col border-r">
          <div className="border-b px-4 py-3">
            <h2 className="text-sm font-semibold">CRM</h2>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <ListSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
      {/* Tab sidebar */}
      <div className="hidden flex-col border-r md:flex md:w-[180px]">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">CRM</h2>
        </div>
        <nav className="flex-1 p-2" aria-label="CRM 탭">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              role="tab"
              aria-selected={activeTab === id}
              className={`flex w-full items-center gap-2 rounded px-3 py-2 text-sm transition-colors ${
                activeTab === id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Mobile tabs */}
      <div className="flex overflow-x-auto border-b md:hidden" role="tablist" aria-label="CRM 탭">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            role="tab"
            aria-selected={activeTab === id}
            className={`flex items-center gap-1 whitespace-nowrap px-4 py-2 text-sm ${
              activeTab === id
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        {activeTab === "events" && <EventsTab />}
        {activeTab === "surveys" && <SurveysTab />}
      </div>
    </div>
  );
}
