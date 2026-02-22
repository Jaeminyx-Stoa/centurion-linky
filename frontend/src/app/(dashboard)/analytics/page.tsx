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
  Filter,
  DollarSign,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useAnalyticsStore } from "@/stores/analytics";
import { useT } from "@/i18n";
import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type TabId = "overview" | "performance" | "satisfaction" | "crm" | "funnel" | "revenue" | "churn";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "overview", label: "Overview", icon: BarChart3 },
  { id: "performance", label: "상담 성과", icon: Target },
  { id: "satisfaction", label: "만족도", icon: Heart },
  { id: "crm", label: "CRM 통계", icon: Activity },
  { id: "funnel", label: "전환 분석", icon: Filter },
  { id: "revenue", label: "매출 분석", icon: DollarSign },
  { id: "churn", label: "이탈 위험", icon: Users },
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

interface FunnelGroup {
  dimension: string;
  conversations: number;
  bookings: number;
  payments: number;
  booking_rate: number;
  payment_rate: number;
}

interface FunnelData {
  days: number;
  group_by: string;
  groups: FunnelGroup[];
  totals: {
    conversations: number;
    bookings: number;
    payments: number;
    booking_rate: number;
    payment_rate: number;
  };
}

function rateColor(rate: number) {
  if (rate >= 30) return "text-green-600";
  if (rate >= 15) return "text-yellow-600";
  return "text-red-600";
}

function FunnelTab() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const [days, setDays] = useState(30);
  const [groupBy, setGroupBy] = useState<"nationality" | "channel" | "both">(
    "nationality",
  );
  const [data, setData] = useState<FunnelData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    api
      .get<FunnelData>(
        `/api/v1/analytics/conversion-funnel?days=${days}&group_by=${groupBy}`,
        { token: accessToken },
      )
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [accessToken, days, groupBy]);

  const DAY_OPTIONS = [7, 14, 30, 60, 90];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {t("analytics.funnel.groupBy")}:
          </span>
          <div className="flex rounded-lg border">
            {(["nationality", "channel", "both"] as const).map((g) => (
              <button
                key={g}
                onClick={() => setGroupBy(g)}
                className={`px-3 py-1 text-xs transition-colors ${
                  groupBy === g
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                {t(`analytics.funnel.${g}`)}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded border px-3 py-1.5 text-sm"
          >
            {DAY_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {d}{t("analytics.funnel.days")}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
      ) : !data || data.groups.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
      ) : (
        <>
          {/* Totals */}
          <div className="grid grid-cols-5 gap-4">
            <StatCard
              label={t("analytics.funnel.conversations")}
              value={data.totals.conversations}
              icon={BarChart3}
            />
            <StatCard
              label={t("analytics.funnel.bookings")}
              value={data.totals.bookings}
              icon={CheckCircle}
              color="text-blue-500"
            />
            <StatCard
              label={t("analytics.funnel.payments")}
              value={data.totals.payments}
              icon={Target}
              color="text-green-500"
            />
            <StatCard
              label={t("analytics.funnel.bookingRate")}
              value={`${data.totals.booking_rate}%`}
              icon={TrendingUp}
              color="text-purple-500"
            />
            <StatCard
              label={t("analytics.funnel.paymentRate")}
              value={`${data.totals.payment_rate}%`}
              icon={Activity}
              color="text-orange-500"
            />
          </div>

          {/* Detail Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {t("analytics.funnel.title")}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-2 text-left font-medium">
                      {groupBy === "nationality"
                        ? t("analytics.funnel.nationality")
                        : groupBy === "channel"
                          ? t("analytics.funnel.channel")
                          : t("analytics.funnel.both")}
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      {t("analytics.funnel.conversations")}
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      {t("analytics.funnel.bookings")}
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      {t("analytics.funnel.payments")}
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      {t("analytics.funnel.bookingRate")}
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      {t("analytics.funnel.paymentRate")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.groups.map((group) => (
                    <tr
                      key={group.dimension}
                      className="border-b last:border-b-0 hover:bg-muted/50"
                    >
                      <td className="px-4 py-2 font-medium">
                        {group.dimension}
                      </td>
                      <td className="px-4 py-2 text-right">
                        {group.conversations}
                      </td>
                      <td className="px-4 py-2 text-right">
                        {group.bookings}
                      </td>
                      <td className="px-4 py-2 text-right">
                        {group.payments}
                      </td>
                      <td
                        className={`px-4 py-2 text-right font-medium ${rateColor(group.booking_rate)}`}
                      >
                        {group.booking_rate}%
                      </td>
                      <td
                        className={`px-4 py-2 text-right font-medium ${rateColor(group.payment_rate)}`}
                      >
                        {group.payment_rate}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

interface ProcedureProfit {
  procedure_id: string;
  procedure_name: string;
  case_count: number;
  total_revenue: number;
  avg_ticket: number;
  total_material_cost: number;
  gross_margin: number;
  margin_rate: number;
}

interface CLVCustomer {
  customer_id: string;
  customer_name: string;
  country_code: string;
  total_payments: number;
  visit_count: number;
  avg_ticket: number;
  predicted_annual_value: number;
}

interface HeatmapCell {
  day_of_week: number;
  hour: number;
  count: number;
  total_amount: number;
}

const DAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];

function marginColor(rate: number) {
  if (rate >= 70) return "text-green-600";
  if (rate >= 40) return "text-yellow-600";
  return "text-red-600";
}

function RevenueTab() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const [days, setDays] = useState(30);
  const [profitData, setProfitData] = useState<ProcedureProfit[]>([]);
  const [clvData, setClvData] = useState<CLVCustomer[]>([]);
  const [natAvg, setNatAvg] = useState<{ country_code: string; avg_clv: number; customer_count: number }[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapCell[]>([]);
  const [peakSlots, setPeakSlots] = useState<HeatmapCell[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    Promise.all([
      api.get<{ procedures: ProcedureProfit[] }>(
        `/api/v1/analytics/procedure-profitability?days=${days}`,
        { token: accessToken },
      ),
      api.get<{ customers: CLVCustomer[]; nationality_avg: typeof natAvg }>(
        `/api/v1/analytics/customer-lifetime-value?days=${Math.max(days, 30)}`,
        { token: accessToken },
      ),
      api.get<{ heatmap: HeatmapCell[]; peak_slots: HeatmapCell[] }>(
        `/api/v1/analytics/revenue-heatmap?days=${days}`,
        { token: accessToken },
      ),
    ])
      .then(([profitRes, clvRes, heatRes]) => {
        setProfitData(profitRes.procedures);
        setClvData(clvRes.customers);
        setNatAvg(clvRes.nationality_avg);
        setHeatmap(heatRes.heatmap);
        setPeakSlots(heatRes.peak_slots);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [accessToken, days]);

  // Build heatmap grid
  const maxAmount = Math.max(...heatmap.map((c) => c.total_amount), 1);
  const heatmapGrid: Record<string, HeatmapCell> = {};
  for (const cell of heatmap) {
    heatmapGrid[`${cell.day_of_week}-${cell.hour}`] = cell;
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <div className="space-y-6">
      {/* Period selector */}
      <div className="flex items-center gap-2">
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded border px-3 py-1.5 text-sm"
        >
          {[7, 14, 30, 60, 90, 180, 365].map((d) => (
            <option key={d} value={d}>
              {d}{t("analytics.funnel.days")}
            </option>
          ))}
        </select>
      </div>

      {/* Procedure Profitability */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("analytics.revenue.procedureProfit")}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {profitData.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">{t("common.noData")}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">{t("analytics.revenue.procedureName")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("analytics.revenue.cases")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("analytics.revenue.totalRevenue")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("analytics.revenue.materialCost")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("analytics.revenue.grossMargin")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("analytics.revenue.marginRate")}</th>
                </tr>
              </thead>
              <tbody>
                {profitData.map((p) => (
                  <tr key={p.procedure_id} className="border-b last:border-b-0 hover:bg-muted/50">
                    <td className="px-4 py-2 font-medium">{p.procedure_name}</td>
                    <td className="px-4 py-2 text-right">{p.case_count}</td>
                    <td className="px-4 py-2 text-right">{p.total_revenue.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right">{p.total_material_cost.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right">{p.gross_margin.toLocaleString()}</td>
                    <td className={`px-4 py-2 text-right font-medium ${marginColor(p.margin_rate)}`}>
                      {p.margin_rate}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* CLV */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("analytics.revenue.clv")}</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {clvData.length === 0 ? (
              <p className="p-4 text-sm text-muted-foreground">{t("common.noData")}</p>
            ) : (
              <div className="divide-y">
                {clvData.slice(0, 10).map((c) => (
                  <div key={c.customer_id} className="flex items-center justify-between px-4 py-2">
                    <div>
                      <p className="text-sm font-medium">{c.customer_name || c.customer_id.slice(0, 8)}</p>
                      <p className="text-xs text-muted-foreground">
                        {c.country_code} | {c.visit_count}{t("analytics.revenue.visitCount")}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{c.total_payments.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">
                        {t("analytics.revenue.predictedAnnual")}: {c.predicted_annual_value.toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("analytics.revenue.nationalityAvg")}</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {natAvg.length === 0 ? (
              <p className="p-4 text-sm text-muted-foreground">{t("common.noData")}</p>
            ) : (
              <div className="divide-y">
                {natAvg.map((n) => (
                  <div key={n.country_code} className="flex items-center justify-between px-4 py-2">
                    <span className="text-sm font-medium">{n.country_code}</span>
                    <div className="text-right">
                      <span className="text-sm">{n.avg_clv.toLocaleString()}</span>
                      <span className="ml-2 text-xs text-muted-foreground">({n.customer_count}명)</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Revenue Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("analytics.revenue.heatmap")}</CardTitle>
        </CardHeader>
        <CardContent>
          {heatmap.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <div className="inline-grid gap-0.5" style={{ gridTemplateColumns: `60px repeat(24, 1fr)` }}>
                  {/* Header row: hours */}
                  <div />
                  {Array.from({ length: 24 }, (_, h) => (
                    <div key={h} className="text-center text-[10px] text-muted-foreground">
                      {h}
                    </div>
                  ))}

                  {/* Data rows */}
                  {Array.from({ length: 7 }, (_, d) => (
                    <>
                      <div key={`label-${d}`} className="flex items-center text-xs font-medium">
                        {DAY_NAMES[d]}
                      </div>
                      {Array.from({ length: 24 }, (_, h) => {
                        const cell = heatmapGrid[`${d}-${h}`];
                        const intensity = cell
                          ? Math.min(cell.total_amount / maxAmount, 1)
                          : 0;
                        return (
                          <div
                            key={`${d}-${h}`}
                            className="aspect-square rounded-sm border"
                            style={{
                              backgroundColor: intensity > 0
                                ? `rgba(59, 130, 246, ${0.1 + intensity * 0.8})`
                                : undefined,
                            }}
                            title={cell ? `${DAY_NAMES[d]} ${h}시: ${cell.count}건, ${cell.total_amount.toLocaleString()}원` : ""}
                          />
                        );
                      })}
                    </>
                  ))}
                </div>
              </div>

              {/* Peak Slots */}
              {peakSlots.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium">{t("analytics.revenue.peakSlots")}</p>
                  <div className="flex flex-wrap gap-2">
                    {peakSlots.map((slot, idx) => (
                      <span
                        key={idx}
                        className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700"
                      >
                        {DAY_NAMES[slot.day_of_week]} {slot.hour}시 — {slot.total_amount.toLocaleString()}원 ({slot.count}건)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

interface ChurnCustomer {
  customer_id: string;
  customer_name: string | null;
  country_code: string | null;
  last_visit: string | null;
  days_since_last_visit: number;
  visit_count: number;
  total_payments: number;
  procedure_name: string | null;
  expected_revisit_days: number | null;
  overdue_days: number;
  churn_risk_score: number;
  risk_level: string;
  revisit_intention: string | null;
}

interface ChurnData {
  total_at_risk: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  customers: ChurnCustomer[];
}

interface RevisitSummaryData {
  total_customers: number;
  due_this_week: number;
  due_this_month: number;
  overdue: number;
  avg_churn_risk: number;
}

function riskBadge(level: string) {
  const colors: Record<string, string> = {
    critical: "bg-red-100 text-red-700",
    high: "bg-orange-100 text-orange-700",
    medium: "bg-yellow-100 text-yellow-700",
    low: "bg-green-100 text-green-700",
  };
  return colors[level] || "bg-gray-100 text-gray-700";
}

function ChurnRiskTab() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const [data, setData] = useState<ChurnData | null>(null);
  const [summary, setSummary] = useState<RevisitSummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [minRisk, setMinRisk] = useState(30);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    Promise.all([
      api.get<ChurnData>(
        `/api/v1/analytics/churn-risk?min_risk=${minRisk}`,
        { token: accessToken },
      ),
      api.get<RevisitSummaryData>(
        "/api/v1/analytics/revisit-summary",
        { token: accessToken },
      ),
    ])
      .then(([churnRes, summaryRes]) => {
        setData(churnRes);
        setSummary(summaryRes);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [accessToken, minRisk]);

  if (loading) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-5 gap-4">
          <StatCard label={t("churn.totalCustomers")} value={summary.total_customers} icon={Users} />
          <StatCard label={t("churn.dueThisWeek")} value={summary.due_this_week} icon={Clock} color="text-yellow-500" />
          <StatCard label={t("churn.dueThisMonth")} value={summary.due_this_month} icon={Clock} color="text-blue-500" />
          <StatCard label={t("churn.overdue")} value={summary.overdue} icon={AlertCircle} color="text-red-500" />
          <StatCard label={t("churn.avgRisk")} value={`${summary.avg_churn_risk}%`} icon={Activity} color="text-orange-500" />
        </div>
      )}

      {/* Risk Level Filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">{t("churn.minRisk")}:</span>
        <select
          value={minRisk}
          onChange={(e) => setMinRisk(Number(e.target.value))}
          className="rounded border px-3 py-1.5 text-sm"
        >
          {[0, 30, 50, 75].map((r) => (
            <option key={r} value={r}>{r}+</option>
          ))}
        </select>
      </div>

      {/* Risk Distribution */}
      {data && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label={t("churn.critical")} value={data.critical_count} icon={AlertCircle} color="text-red-500" />
          <StatCard label={t("churn.high")} value={data.high_count} icon={TrendingUp} color="text-orange-500" />
          <StatCard label={t("churn.medium")} value={data.medium_count} icon={Activity} color="text-yellow-500" />
        </div>
      )}

      {/* Customer List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("churn.atRiskCustomers")}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {!data || data.customers.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">{t("common.noData")}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">{t("churn.customer")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("churn.lastVisit")}</th>
                  <th className="px-4 py-2 text-left font-medium">{t("churn.lastProcedure")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("churn.overdueDays")}</th>
                  <th className="px-4 py-2 text-right font-medium">{t("churn.riskScore")}</th>
                  <th className="px-4 py-2 text-center font-medium">{t("churn.level")}</th>
                </tr>
              </thead>
              <tbody>
                {data.customers.map((c) => (
                  <tr key={c.customer_id} className="border-b last:border-b-0 hover:bg-muted/50">
                    <td className="px-4 py-2">
                      <div>
                        <p className="font-medium">{c.customer_name || c.customer_id.slice(0, 8)}</p>
                        <p className="text-xs text-muted-foreground">{c.country_code || ""}</p>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-right">
                      {c.last_visit || "-"}
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({c.days_since_last_visit}{t("analytics.funnel.days")})
                      </span>
                    </td>
                    <td className="px-4 py-2">{c.procedure_name || "-"}</td>
                    <td className="px-4 py-2 text-right">
                      {c.overdue_days > 0 ? (
                        <span className="text-red-600">+{c.overdue_days}{t("analytics.funnel.days")}</span>
                      ) : (
                        <span className="text-green-600">-</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-right font-medium">{c.churn_risk_score}</td>
                    <td className="px-4 py-2 text-center">
                      <span className={`rounded px-2 py-0.5 text-xs ${riskBadge(c.risk_level)}`}>
                        {c.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
        {activeTab === "funnel" && <FunnelTab />}
        {activeTab === "revenue" && <RevenueTab />}
        {activeTab === "churn" && <ChurnRiskTab />}
      </div>
    </div>
  );
}
