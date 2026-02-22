"use client";

import { useEffect, useState } from "react";
import {
  FileText,
  Plus,
  ClipboardList,
  FileCheck,
  Trash2,
  CheckCircle,
  Eye,
  PenLine,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useMedicalDocumentStore } from "@/stores/medical-document";
import { useT } from "@/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { MedicalDocument, ChartDraftContent } from "@/types/medical-document";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-yellow-100 text-yellow-700",
  reviewed: "bg-blue-100 text-blue-700",
  signed: "bg-green-100 text-green-700",
  archived: "bg-gray-100 text-gray-500",
};

function DocumentDetail({ doc, onClose }: { doc: MedicalDocument; onClose: () => void }) {
  const { accessToken } = useAuthStore();
  const t = useT();
  const { updateStatus } = useMedicalDocumentStore();

  const handleStatus = async (status: string) => {
    if (!accessToken) return;
    await updateStatus(accessToken, doc.id, status);
  };

  const content = doc.content as ChartDraftContent | null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">{doc.title}</CardTitle>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          &times;
        </button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLORS[doc.status] || ""}`}>
            {t(`documents.status.${doc.status}` as never)}
          </span>
          <span className="text-xs text-muted-foreground">
            {doc.generated_by === "ai" ? "AI" : "Staff"} | {doc.language.toUpperCase()}
          </span>
        </div>

        {doc.document_type === "chart_draft" && content && (
          <div className="space-y-3 text-sm">
            {content.chief_complaint && (
              <div>
                <Label className="text-xs text-muted-foreground">{t("documents.chiefComplaint")}</Label>
                <p>{content.chief_complaint}</p>
              </div>
            )}
            {content.desired_procedures && content.desired_procedures.length > 0 && (
              <div>
                <Label className="text-xs text-muted-foreground">{t("documents.desiredProcedures")}</Label>
                <p>{content.desired_procedures.join(", ")}</p>
              </div>
            )}
            {content.medical_history && (
              <div>
                <Label className="text-xs text-muted-foreground">{t("documents.medicalHistory")}</Label>
                <p>{content.medical_history}</p>
              </div>
            )}
            {content.allergies && (
              <div>
                <Label className="text-xs text-muted-foreground">Allergies</Label>
                <p>{content.allergies}</p>
              </div>
            )}
            {content.skin_type && (
              <div>
                <Label className="text-xs text-muted-foreground">{t("documents.skinType")}</Label>
                <p>{content.skin_type}</p>
              </div>
            )}
            {content.ai_recommendations && (
              <div>
                <Label className="text-xs text-muted-foreground">{t("documents.aiRecommendations")}</Label>
                <p>{content.ai_recommendations}</p>
              </div>
            )}
          </div>
        )}

        {doc.document_type === "consent_form" && content && (
          <div className="space-y-3 text-sm">
            <pre className="whitespace-pre-wrap rounded bg-muted p-3 text-xs">
              {JSON.stringify(content, null, 2)}
            </pre>
          </div>
        )}

        <div className="flex gap-2 border-t pt-3">
          {doc.status === "draft" && (
            <Button size="sm" variant="outline" onClick={() => handleStatus("reviewed")}>
              <Eye className="mr-1 h-3 w-3" />
              {t("documents.status.reviewed")}
            </Button>
          )}
          {doc.status === "reviewed" && (
            <Button size="sm" variant="outline" onClick={() => handleStatus("signed")}>
              <PenLine className="mr-1 h-3 w-3" />
              {t("documents.status.signed")}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DocumentsPage() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const { documents, total, isLoading, fetchDocuments, generateChartDraft, generateConsentForm, deleteDocument } =
    useMedicalDocumentStore();
  const [selectedDoc, setSelectedDoc] = useState<MedicalDocument | null>(null);
  const [filterType, setFilterType] = useState<string>("");
  const [showGenerate, setShowGenerate] = useState(false);
  const [genType, setGenType] = useState<"chart" | "consent">("chart");
  const [genId, setGenId] = useState("");
  const [genLang, setGenLang] = useState("ko");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (accessToken) {
      fetchDocuments(accessToken, {
        document_type: filterType || undefined,
      });
    }
  }, [accessToken, fetchDocuments, filterType]);

  const handleGenerate = async () => {
    if (!accessToken || !genId.trim()) return;
    setGenerating(true);
    try {
      if (genType === "chart") {
        await generateChartDraft(accessToken, genId.trim());
      } else {
        await generateConsentForm(accessToken, genId.trim(), genLang);
      }
      setShowGenerate(false);
      setGenId("");
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!accessToken) return;
    await deleteDocument(accessToken, id);
    if (selectedDoc?.id === id) setSelectedDoc(null);
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">{t("documents.title")}</h1>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowGenerate(!showGenerate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          {t("documents.generate")}
        </Button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* List */}
        <div className="flex w-full flex-col overflow-hidden md:w-1/2">
          {/* Filter bar */}
          <div className="flex items-center gap-2 border-b px-4 py-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="rounded border px-2 py-1 text-xs"
            >
              <option value="">All</option>
              <option value="chart_draft">{t("documents.chartDraft")}</option>
              <option value="consent_form">{t("documents.consentForm")}</option>
            </select>
            <span className="text-xs text-muted-foreground">
              {total} {t("documents.title").toLowerCase()}
            </span>
          </div>

          {showGenerate && (
            <div className="border-b p-4">
              <Card>
                <CardContent className="space-y-3 pt-4">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant={genType === "chart" ? "default" : "outline"}
                      onClick={() => setGenType("chart")}
                    >
                      <ClipboardList className="mr-1 h-3 w-3" />
                      {t("documents.generateChartDraft")}
                    </Button>
                    <Button
                      size="sm"
                      variant={genType === "consent" ? "default" : "outline"}
                      onClick={() => setGenType("consent")}
                    >
                      <FileCheck className="mr-1 h-3 w-3" />
                      {t("documents.generateConsentForm")}
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <Label>
                      {genType === "chart"
                        ? t("documents.selectConversation")
                        : t("documents.selectBooking")}
                    </Label>
                    <Input
                      value={genId}
                      onChange={(e) => setGenId(e.target.value)}
                      placeholder="UUID"
                    />
                  </div>
                  {genType === "consent" && (
                    <div className="space-y-2">
                      <Label>{t("documents.language")}</Label>
                      <select
                        value={genLang}
                        onChange={(e) => setGenLang(e.target.value)}
                        className="w-full rounded border px-3 py-2 text-sm"
                      >
                        <option value="ko">한국어</option>
                        <option value="en">English</option>
                        <option value="ja">日本語</option>
                        <option value="zh">中文</option>
                        <option value="vi">Tiếng Việt</option>
                      </select>
                    </div>
                  )}
                  <Button
                    size="sm"
                    onClick={handleGenerate}
                    disabled={generating}
                  >
                    {generating ? "Generating..." : t("documents.generate")}
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="flex-1 overflow-y-auto">
            {documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                <FileText className="mb-2 h-8 w-8" />
                <p className="text-sm">{t("documents.empty")}</p>
              </div>
            ) : (
              <div className="divide-y">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc)}
                    className={`flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-muted/50 ${
                      selectedDoc?.id === doc.id ? "bg-muted/50" : ""
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {doc.document_type === "chart_draft" ? (
                          <ClipboardList className="h-4 w-4 text-blue-500" />
                        ) : (
                          <FileCheck className="h-4 w-4 text-green-500" />
                        )}
                        <p className="truncate text-sm font-medium">{doc.title}</p>
                      </div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        <span className={`rounded px-1.5 py-0.5 ${STATUS_COLORS[doc.status] || ""}`}>
                          {doc.status}
                        </span>
                        {doc.customer_name && <span>{doc.customer_name}</span>}
                        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(doc.id);
                      }}
                      className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="hidden flex-1 overflow-y-auto border-l p-4 md:block">
          {selectedDoc ? (
            <DocumentDetail doc={selectedDoc} onClose={() => setSelectedDoc(null)} />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <p className="text-sm">Select a document to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
