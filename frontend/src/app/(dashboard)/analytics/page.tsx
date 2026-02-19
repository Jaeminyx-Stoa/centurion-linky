"use client";

import { useEffect } from "react";
import {
  BarChart3,
  TrendingUp,
  Users,
  ThumbsUp,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useAnalyticsStore } from "@/stores/analytics";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

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

export default function AnalyticsPage() {
  const { accessToken } = useAuthStore();
  const {
    dashboard,
    satisfactionTrend,
    nps,
    revisitRate,
    isLoading,
    error,
    fetchAll,
  } = useAnalyticsStore();

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

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center text-destructive">
        <AlertCircle className="mr-2 h-5 w-5" />
        {error}
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <h1 className="text-xl font-bold">통계 대시보드</h1>

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

          {/* Event Status Breakdown */}
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
    </div>
  );
}
