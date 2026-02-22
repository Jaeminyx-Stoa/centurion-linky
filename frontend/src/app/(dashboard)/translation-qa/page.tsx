"use client";

import { useEffect, useState } from "react";
import {
  Languages,
  AlertCircle,
  CheckCircle,
  Clock,
  FileWarning,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useTranslationReportStore } from "@/stores/translation-report";
import { useT } from "@/i18n";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type TabId = "dashboard" | "reports" | "pending";

const TABS: { id: TabId; label: string }[] = [
  { id: "dashboard", label: "QA 대시보드" },
  { id: "reports", label: "전체 리포트" },
  { id: "pending", label: "검토 대기" },
];

const ERROR_TYPE_LABELS: Record<string, string> = {
  wrong_term: "용어 오류",
  wrong_meaning: "의미 오류",
  awkward: "부자연스러움",
  omission: "누락",
  other: "기타",
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  minor: "bg-yellow-100 text-yellow-700",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  reviewed: "bg-blue-100 text-blue-700",
  resolved: "bg-green-100 text-green-700",
  dismissed: "bg-gray-100 text-gray-500",
};

export default function TranslationQAPage() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const { reports, total, stats, isLoading, fetchReports, fetchStats, reviewReport } =
    useTranslationReportStore();
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");

  useEffect(() => {
    if (!accessToken) return;
    fetchStats(accessToken);
    if (activeTab === "reports") {
      fetchReports(accessToken);
    } else if (activeTab === "pending") {
      fetchReports(accessToken, { status: "pending" });
    }
  }, [accessToken, activeTab, fetchReports, fetchStats]);

  const handleReview = async (reportId: string, status: string) => {
    if (!accessToken) return;
    await reviewReport(accessToken, reportId, { status });
    if (activeTab === "pending") {
      fetchReports(accessToken, { status: "pending" });
    } else {
      fetchReports(accessToken);
    }
    fetchStats(accessToken);
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="border-b px-6 py-3">
        <h1 className="text-lg font-semibold">{t("translationQA.title")}</h1>
      </div>

      {/* Tabs */}
      <div className="flex border-b px-6" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`px-4 py-2 text-sm ${
              activeTab === tab.id
                ? "border-b-2 border-primary text-primary font-medium"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "dashboard" && stats && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{t("translationQA.totalReports")}</p>
                      <p className="text-2xl font-bold">{stats.total_reports}</p>
                    </div>
                    <FileWarning className="h-8 w-8 text-orange-500 opacity-70" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{t("translationQA.pending")}</p>
                      <p className="text-2xl font-bold">{stats.pending_count}</p>
                    </div>
                    <Clock className="h-8 w-8 text-yellow-500 opacity-70" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{t("translationQA.resolved")}</p>
                      <p className="text-2xl font-bold">{stats.resolved_count}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500 opacity-70" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{t("translationQA.accuracy")}</p>
                      <p className="text-2xl font-bold">
                        {stats.accuracy_score !== null ? `${stats.accuracy_score}%` : "-"}
                      </p>
                    </div>
                    <Languages className="h-8 w-8 text-blue-500 opacity-70" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Error Type Breakdown */}
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("translationQA.byErrorType")}</CardTitle>
                </CardHeader>
                <CardContent>
                  {Object.keys(stats.by_error_type).length === 0 ? (
                    <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
                  ) : (
                    <div className="space-y-2">
                      {Object.entries(stats.by_error_type).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between text-sm">
                          <span>{ERROR_TYPE_LABELS[type] || type}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("translationQA.byLanguage")}</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats.by_language_pair.length === 0 ? (
                    <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
                  ) : (
                    <div className="space-y-2">
                      {stats.by_language_pair.map((lp) => (
                        <div
                          key={`${lp.source}-${lp.target}`}
                          className="flex items-center justify-between text-sm"
                        >
                          <span>
                            {lp.source} → {lp.target}
                          </span>
                          <span className="font-medium">{lp.count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {(activeTab === "reports" || activeTab === "pending") && (
          <div className="space-y-4">
            {isLoading ? (
              <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
            ) : reports.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("translationQA.empty")}</p>
            ) : (
              <div className="space-y-3">
                {reports.map((report) => (
                  <Card key={report.id}>
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`rounded px-2 py-0.5 text-xs ${SEVERITY_COLORS[report.severity] || ""}`}>
                              {report.severity}
                            </span>
                            <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLORS[report.status] || ""}`}>
                              {report.status}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {ERROR_TYPE_LABELS[report.error_type] || report.error_type}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {report.source_language} → {report.target_language}
                            </span>
                          </div>
                          <div className="space-y-1 text-sm">
                            <p>
                              <span className="font-medium">{t("translationQA.original")}:</span>{" "}
                              {report.original_text}
                            </p>
                            <p>
                              <span className="font-medium">{t("translationQA.translated")}:</span>{" "}
                              <span className="text-red-600">{report.translated_text}</span>
                            </p>
                            {report.corrected_text && (
                              <p>
                                <span className="font-medium">{t("translationQA.corrected")}:</span>{" "}
                                <span className="text-green-600">{report.corrected_text}</span>
                              </p>
                            )}
                          </div>
                        </div>
                        {report.status === "pending" && (
                          <div className="flex gap-1 ml-4">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                              onClick={() => handleReview(report.id, "resolved")}
                            >
                              {t("translationQA.resolve")}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 text-xs"
                              onClick={() => handleReview(report.id, "dismissed")}
                            >
                              {t("translationQA.dismiss")}
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
