"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Users,
  ThumbsUp,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Target,
  Heart,
  Activity,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useAnalyticsStore } from "@/stores/analytics";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type TabId = "overview" | "performance" | "satisfaction" | "crm";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "overview", label: "Overview", icon: BarChart3 },
  { id: "performance", label: "상담 성과", icon: Target },
  { id: "satisfaction", label: "만족도", icon: Heart },
  { id: "crm", label: "CRM 통계", icon: Activity },
];

function StatCard({
  label,
  value,
  icon: Icon,
  color = "text-primary",
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color?: string;
}) {
  return (
    <Card>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
          <Icon className={`h-8 w-8 ${color} opacity-70`} />
        </div>
      </CardContent>
    </Card>
  );
}

function NPSBar({
  label,
  value,
  total,
  color,
}: {
  label: string;
  value: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="text-muted-foreground">
          {value}명 ({pct}%)
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function OverviewTab() {
  const {
    overview,
    dashboard,
  } = useAnalyticsStore();

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="총 대화"
            value={overview.total_conversations}
            icon={BarChart3}
          />
          <StatCard
            label="총 고객"
            value={overview.total_customers}
            icon={Users}
            color="text-blue-500"
          />
          <StatCard
            label="총 예약"
            value={overview.total_bookings}
            icon={CheckCircle}
            color="text-green-500"
          />
        </div>
      )}

      {/* CRM Dashboard Stats */}
      {dashboard && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <StatCard
              label="전체 이벤트"
              value={dashboard.total_events}
              icon={BarChart3}
            />
            <StatCard
              label="설문 수"
              value={dashboard.total_surveys}
              icon={Users}
              color="text-blue-500"
            />
            <StatCard
              label="평균 만족도"
              value={
                dashboard.avg_satisfaction !== null
                  ? dashboard.avg_satisfaction.toFixed(1)
                  : "-"
              }
              icon={ThumbsUp}
              color="text-green-500"
            />
            <StatCard
              label="평균 NPS"
              value={
                dashboard.avg_nps !== null
                  ? dashboard.avg_nps.toFixed(1)
                  : "-"
              }
              icon={TrendingUp}
              color="text-purple-500"
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">CRM 이벤트 현황</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-500" />
                  <div>
                    <p className="text-sm text-muted-foreground">예정</p>
                    <p className="text-lg font-semibold">
                      {dashboard.scheduled}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-yellow-500" />
                  <div>
                    <p className="text-sm text-muted-foreground">발송</p>
                    <p className="text-lg font-semibold">{dashboard.sent}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <div>
                    <p className="text-sm text-muted-foreground">완료</p>
                    <p className="text-lg font-semibold">
                      {dashboard.completed}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-muted-foreground">취소</p>
                    <p className="text-lg font-semibold">
                      {dashboard.cancelled}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <div>
                    <p className="text-sm text-muted-foreground">실패</p>
                    <p className="text-lg font-semibold">
                      {dashboard.failed}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function PerformanceTab() {
  const { accessToken } = useAuthStore();
  const { consultationPerformance, fetchConsultationPerformance } =
    useAnalyticsStore();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  useEffect(() => {
    if (accessToken) {
      fetchConsultationPerformance(accessToken, year, month);
    }
  }, [accessToken, year, month, fetchConsultationPerformance]);

  const cp = consultationPerformance;

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center gap-2">
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="rounded border px-3 py-1.5 text-sm"
        >
          {[2024, 2025, 2026].map((y) => (
            <option key={y} value={y}>
              {y}년
            </option>
          ))}
        </select>
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          className="rounded border px-3 py-1.5 text-sm"
        >
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <option key={m} value={m}>
              {m}월
            </option>
          ))}
        </select>
      </div>

      {cp ? (
        <>
          <div className="grid grid-cols-4 gap-4">
            <StatCard
              label="총점"
              value={cp.total_score.toFixed(1)}
              icon={Target}
            />
            <StatCard
              label="세일즈 믹스"
              value={cp.sales_mix_score.toFixed(1)}
              icon={TrendingUp}
              color="text-blue-500"
            />
            <StatCard
              label="예약 전환"
              value={cp.booking_conversion_score.toFixed(1)}
              icon={CheckCircle}
              color="text-green-500"
            />
            <StatCard
              label="결제 전환"
              value={cp.payment_conversion_score.toFixed(1)}
              icon={Activity}
              color="text-purple-500"
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">상세 지표</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold">
                    {cp.total_conversations}
                  </p>
                  <p className="text-sm text-muted-foreground">총 상담</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{cp.total_bookings}</p>
                  <p className="text-sm text-muted-foreground">총 예약</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{cp.total_payments}</p>
                  <p className="text-sm text-muted-foreground">총 결제</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          해당 기간의 데이터가 없습니다
        </p>
      )}
    </div>
  );
}

function SatisfactionTab() {
  const { satisfactionTrend, nps, revisitRate, satisfactionAlerts } =
    useAnalyticsStore();
  const { accessToken } = useAuthStore();
  const { fetchSatisfactionAlerts } = useAnalyticsStore();

  useEffect(() => {
    if (accessToken) {
      fetchSatisfactionAlerts(accessToken);
    }
  }, [accessToken, fetchSatisfactionAlerts]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        {/* Satisfaction Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">만족도 추이 (라운드별)</CardTitle>
          </CardHeader>
          <CardContent>
            {satisfactionTrend.length === 0 ? (
              <p className="text-sm text-muted-foreground">데이터 없음</p>
            ) : (
              <div className="space-y-3">
                {satisfactionTrend.map((item) => (
                  <div key={item.round} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{item.round}차 설문</span>
                      <span className="font-medium">
                        평균 {item.avg_score.toFixed(1)}점 ({item.count}건)
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-green-500"
                        style={{
                          width: `${(item.avg_score / 5) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* NPS */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">NPS (순 추천 지수)</CardTitle>
          </CardHeader>
          <CardContent>
            {!nps || nps.total === 0 ? (
              <p className="text-sm text-muted-foreground">데이터 없음</p>
            ) : (
              <div className="space-y-4">
                <div className="text-center">
                  <p className="text-4xl font-bold">{nps.nps}</p>
                  <p className="text-sm text-muted-foreground">
                    NPS 점수 (총 {nps.total}명)
                  </p>
                </div>
                <div className="space-y-2">
                  <NPSBar
                    label="추천 (9-10)"
                    value={nps.promoters}
                    total={nps.total}
                    color="bg-green-500"
                  />
                  <NPSBar
                    label="중립 (7-8)"
                    value={nps.passives}
                    total={nps.total}
                    color="bg-yellow-500"
                  />
                  <NPSBar
                    label="비추천 (0-6)"
                    value={nps.detractors}
                    total={nps.total}
                    color="bg-red-500"
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Revisit Rate */}
      {revisitRate && revisitRate.total > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">재방문 의향</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">
                  {revisitRate.yes_rate.toFixed(0)}%
                </p>
                <p className="text-sm text-muted-foreground">재방문 의향률</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-green-500">
                  {revisitRate.yes}
                </p>
                <p className="text-sm text-muted-foreground">예</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-yellow-500">
                  {revisitRate.maybe}
                </p>
                <p className="text-sm text-muted-foreground">보통</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-red-500">
                  {revisitRate.no}
                </p>
                <p className="text-sm text-muted-foreground">아니오</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Satisfaction Alerts */}
      {satisfactionAlerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">만족도 알림</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {satisfactionAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between rounded border p-3"
                >
                  <div>
                    <p className="text-sm font-medium">
                      대화 {alert.conversation_id.slice(0, 8)}...
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.created_at).toLocaleDateString("ko-KR")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        alert.level === "critical"
                          ? "bg-red-50 text-red-700"
                          : alert.level === "warning"
                            ? "bg-yellow-50 text-yellow-700"
                            : "bg-green-50 text-green-700"
                      }`}
                    >
                      {alert.level}
                    </span>
                    <span className="text-sm font-medium">
                      {alert.score}/5
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CRMStatsTab() {
  const { accessToken } = useAuthStore();
  const { crmEvents, fetchCRMEvents } = useAnalyticsStore();

  useEffect(() => {
    if (accessToken) {
      fetchCRMEvents(accessToken);
    }
  }, [accessToken, fetchCRMEvents]);

  // Group by event_type
  const eventTypeCounts = crmEvents.reduce(
    (acc, e) => {
      acc[e.event_type] = (acc[e.event_type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  // Group by status
  const statusCounts = crmEvents.reduce(
    (acc, e) => {
      acc[e.status] = (acc[e.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">이벤트 타입별 집계</CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(eventTypeCounts).length === 0 ? (
              <p className="text-sm text-muted-foreground">데이터 없음</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(eventTypeCounts).map(([type, count]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between text-sm"
                  >
                    <span>{type}</span>
                    <span className="font-medium">{count}건</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">상태별 집계</CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(statusCounts).length === 0 ? (
              <p className="text-sm text-muted-foreground">데이터 없음</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(statusCounts).map(([status, count]) => (
                  <div
                    key={status}
                    className="flex items-center justify-between text-sm"
                  >
                    <span>{status}</span>
                    <span className="font-medium">{count}건</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Events */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            최근 CRM 이벤트 ({crmEvents.length}건)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {crmEvents.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">이벤트 없음</p>
          ) : (
            <div className="divide-y">
              {crmEvents.slice(0, 20).map((event) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium">{event.event_type}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(event.scheduled_at).toLocaleString("ko-KR")}
                    </p>
                  </div>
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      event.status === "completed"
                        ? "bg-green-50 text-green-700"
                        : event.status === "scheduled"
                          ? "bg-blue-50 text-blue-700"
                          : event.status === "cancelled"
                            ? "bg-gray-100 text-gray-500"
                            : "bg-yellow-50 text-yellow-700"
                    }`}
                  >
                    {event.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AnalyticsPage() {
  const { accessToken } = useAuthStore();
  const { isLoading, error, fetchAll } = useAnalyticsStore();
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  useEffect(() => {
    if (accessToken) {
      fetchAll(accessToken);
    }
  }, [accessToken, fetchAll]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <BarChart3 className="mr-2 h-5 w-5 animate-pulse" />
        통계 로딩 중...
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
      {/* Tab sidebar (desktop) */}
      <div className="hidden md:flex w-[180px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">통계</h2>
        </div>
        <nav className="flex-1 p-2" aria-label="통계 탭">
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
      <div className="flex overflow-x-auto border-b md:hidden" role="tablist" aria-label="통계 탭">
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
        {activeTab === "overview" && <OverviewTab />}
        {activeTab === "performance" && <PerformanceTab />}
        {activeTab === "satisfaction" && <SatisfactionTab />}
        {activeTab === "crm" && <CRMStatsTab />}
      </div>
    </div>
  );
}
