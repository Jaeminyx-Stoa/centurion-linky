"use client";

import { useEffect, useState } from "react";
import { DollarSign, TrendingUp, Zap, AlertCircle } from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useT } from "@/i18n";
import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface MonthlySummary {
  year: number;
  month: number;
  total_cost_usd: number;
  total_tokens: number;
  by_operation: {
    operation: string;
    count: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    cost_usd: number;
  }[];
}

interface DailyData {
  date: string;
  count: number;
  total_tokens: number;
  cost_usd: number;
}

interface QuotaInfo {
  monthly_quota_usd: number | null;
  current_month_cost_usd: number;
  usage_percent: number | null;
  alert_sent: boolean;
}

type TabId = "summary" | "daily" | "quota";

export default function LLMUsagePage() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [dailyData, setDailyData] = useState<DailyData[]>([]);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [quotaInput, setQuotaInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    setIsLoading(true);
    setError(null);

    Promise.all([
      api.get<MonthlySummary>(
        `/api/v1/llm-usage/summary?year=${year}&month=${month}`,
        { token: accessToken },
      ),
      api.get<{ data: DailyData[] }>(
        `/api/v1/llm-usage/daily?days=30`,
        { token: accessToken },
      ),
      api.get<QuotaInfo>(`/api/v1/llm-usage/quota`, { token: accessToken }),
    ])
      .then(([summaryData, dailyResult, quotaData]) => {
        setSummary(summaryData);
        setDailyData(dailyResult.data);
        setQuota(quotaData);
        if (quotaData.monthly_quota_usd != null) {
          setQuotaInput(String(quotaData.monthly_quota_usd));
        }
      })
      .catch(() => setError("Failed to load LLM usage data"))
      .finally(() => setIsLoading(false));
  }, [accessToken, year, month]);

  const handleSetQuota = async () => {
    if (!accessToken) return;
    const val = parseFloat(quotaInput);
    if (isNaN(val) || val <= 0) return;
    try {
      await api.patch(
        `/api/v1/llm-usage/quota`,
        { monthly_quota_usd: val },
        { token: accessToken },
      );
      const updated = await api.get<QuotaInfo>(`/api/v1/llm-usage/quota`, {
        token: accessToken,
      });
      setQuota(updated);
    } catch {
      // silently fail
    }
  };

  const TABS: { id: TabId; label: string }[] = [
    { id: "summary", label: t("llmUsage.tab.summary") },
    { id: "daily", label: t("llmUsage.tab.daily") },
    { id: "quota", label: t("llmUsage.tab.quota") },
  ];

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <DollarSign className="mr-2 h-5 w-5 animate-pulse" />
        {t("common.loading")}
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b px-6 py-3">
        <h1 className="text-lg font-semibold">{t("llmUsage.title")}</h1>
      </div>

      {/* Tabs */}
      <div className="flex border-b" role="tablist">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            role="tab"
            aria-selected={activeTab === id}
            className={`px-4 py-2 text-sm ${
              activeTab === id
                ? "border-b-2 border-primary text-primary font-medium"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
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

        {activeTab === "summary" && (
          <SummaryTab
            summary={summary}
            year={year}
            month={month}
            onYearChange={setYear}
            onMonthChange={setMonth}
            t={t}
          />
        )}
        {activeTab === "daily" && <DailyTab data={dailyData} t={t} />}
        {activeTab === "quota" && (
          <QuotaTab
            quota={quota}
            quotaInput={quotaInput}
            onQuotaInputChange={setQuotaInput}
            onSetQuota={handleSetQuota}
            t={t}
          />
        )}
      </div>
    </div>
  );
}

function SummaryTab({
  summary,
  year,
  month,
  onYearChange,
  onMonthChange,
  t,
}: {
  summary: MonthlySummary | null;
  year: number;
  month: number;
  onYearChange: (y: number) => void;
  onMonthChange: (m: number) => void;
  t: (key: string) => string;
}) {
  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center gap-2">
        <select
          value={year}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="rounded border bg-background px-3 py-1.5 text-sm"
        >
          {[2024, 2025, 2026].map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          value={month}
          onChange={(e) => onMonthChange(Number(e.target.value))}
          className="rounded border bg-background px-3 py-1.5 text-sm"
        >
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <option key={m} value={m}>
              {m}월
            </option>
          ))}
        </select>
      </div>

      {summary && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardContent className="pt-0">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {t("llmUsage.totalCost")}
                    </p>
                    <p className="text-2xl font-bold">
                      ${summary.total_cost_usd.toFixed(4)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-500 opacity-70" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-0">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {t("llmUsage.totalTokens")}
                    </p>
                    <p className="text-2xl font-bold">
                      {summary.total_tokens.toLocaleString()}
                    </p>
                  </div>
                  <Zap className="h-8 w-8 text-yellow-500 opacity-70" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Operation breakdown table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {t("llmUsage.operation")}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {summary.by_operation.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">
                  {t("common.noData")}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="px-4 py-2">{t("llmUsage.operation")}</th>
                        <th className="px-4 py-2 text-right">
                          {t("llmUsage.count")}
                        </th>
                        <th className="px-4 py-2 text-right">
                          {t("llmUsage.inputTokens")}
                        </th>
                        <th className="px-4 py-2 text-right">
                          {t("llmUsage.outputTokens")}
                        </th>
                        <th className="px-4 py-2 text-right">
                          {t("llmUsage.cost")}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.by_operation.map((op) => (
                        <tr key={op.operation} className="border-b last:border-0">
                          <td className="px-4 py-2 font-medium">
                            {op.operation}
                          </td>
                          <td className="px-4 py-2 text-right">{op.count}</td>
                          <td className="px-4 py-2 text-right">
                            {op.input_tokens.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-right">
                            {op.output_tokens.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-right">
                            ${op.cost_usd.toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function DailyTab({
  data,
  t,
}: {
  data: DailyData[];
  t: (key: string) => string;
}) {
  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
    );
  }

  const maxCost = Math.max(...data.map((d) => d.cost_usd), 0.001);

  return (
    <div className="space-y-6">
      {/* Bar chart visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            {t("llmUsage.tab.daily")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-1" style={{ height: 200 }}>
            {data.map((d) => (
              <div
                key={d.date}
                className="flex flex-1 flex-col items-center gap-1"
              >
                <div
                  className="w-full rounded-t bg-primary/70 transition-all hover:bg-primary"
                  style={{
                    height: `${(d.cost_usd / maxCost) * 160}px`,
                    minHeight: d.cost_usd > 0 ? 4 : 0,
                  }}
                  title={`${d.date}: $${d.cost_usd.toFixed(4)}`}
                />
              </div>
            ))}
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-muted-foreground">
            <span>{data[0]?.date}</span>
            <span>{data[data.length - 1]?.date}</span>
          </div>
        </CardContent>
      </Card>

      {/* Daily detail table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="px-4 py-2">{t("llmUsage.date")}</th>
                  <th className="px-4 py-2 text-right">
                    {t("llmUsage.count")}
                  </th>
                  <th className="px-4 py-2 text-right">
                    {t("llmUsage.totalTokens")}
                  </th>
                  <th className="px-4 py-2 text-right">
                    {t("llmUsage.cost")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {[...data].reverse().map((d) => (
                  <tr key={d.date} className="border-b last:border-0">
                    <td className="px-4 py-2">{d.date}</td>
                    <td className="px-4 py-2 text-right">{d.count}</td>
                    <td className="px-4 py-2 text-right">
                      {d.total_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      ${d.cost_usd.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function QuotaTab({
  quota,
  quotaInput,
  onQuotaInputChange,
  onSetQuota,
  t,
}: {
  quota: QuotaInfo | null;
  quotaInput: string;
  onQuotaInputChange: (val: string) => void;
  onSetQuota: () => void;
  t: (key: string) => string;
}) {
  return (
    <div className="space-y-6 max-w-lg">
      {/* Current quota status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("llmUsage.quota")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {quota?.monthly_quota_usd != null ? (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  {t("llmUsage.quota")}
                </span>
                <span className="font-medium">
                  ${quota.monthly_quota_usd.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  {t("llmUsage.currentUsage")}
                </span>
                <span className="font-medium">
                  ${quota.current_month_cost_usd.toFixed(4)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  {t("llmUsage.usagePercent")}
                </span>
                <span
                  className={`font-medium ${
                    (quota.usage_percent ?? 0) >= 100
                      ? "text-red-500"
                      : (quota.usage_percent ?? 0) >= 80
                        ? "text-yellow-500"
                        : "text-green-500"
                  }`}
                >
                  {quota.usage_percent?.toFixed(1) ?? 0}%
                </span>
              </div>
              {/* Usage bar */}
              <div className="h-3 w-full rounded-full bg-muted">
                <div
                  className={`h-full rounded-full transition-all ${
                    (quota.usage_percent ?? 0) >= 100
                      ? "bg-red-500"
                      : (quota.usage_percent ?? 0) >= 80
                        ? "bg-yellow-500"
                        : "bg-green-500"
                  }`}
                  style={{
                    width: `${Math.min(quota.usage_percent ?? 0, 100)}%`,
                  }}
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t("llmUsage.noQuota")}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Set quota */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("llmUsage.setQuota")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                $
              </span>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={quotaInput}
                onChange={(e) => onQuotaInputChange(e.target.value)}
                className="pl-7"
                placeholder="100.00"
              />
            </div>
            <Button onClick={onSetQuota}>{t("common.save")}</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
