"use client";

import { useEffect, useState } from "react";
import {
  Syringe,
  ChevronRight,
  Plus,
  Clock,
  Star,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useProcedureStore } from "@/stores/procedure";
import { Button } from "@/components/ui/button";
import type { ProcedureCategoryTree, ClinicProcedure } from "@/types/procedure";

function CategoryItem({
  category,
  selectedId,
  onSelect,
  depth = 0,
}: {
  category: ProcedureCategoryTree;
  selectedId: string | null;
  onSelect: (id: string) => void;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = category.children.length > 0;

  return (
    <div>
      <button
        onClick={() => {
          onSelect(category.id);
          if (hasChildren) setExpanded(!expanded);
        }}
        className={`flex w-full items-center gap-1 rounded px-2 py-1.5 text-sm transition-colors ${
          selectedId === category.id
            ? "bg-primary text-primary-foreground"
            : "hover:bg-muted"
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {hasChildren && (
          <ChevronRight
            className={`h-3 w-3 transition-transform ${expanded ? "rotate-90" : ""}`}
          />
        )}
        <span className="truncate">{category.name_ko}</span>
      </button>
      {expanded &&
        hasChildren &&
        category.children.map((child) => (
          <CategoryItem
            key={child.id}
            category={child}
            selectedId={selectedId}
            onSelect={onSelect}
            depth={depth + 1}
          />
        ))}
    </div>
  );
}

function ProcedureRow({ cp }: { cp: ClinicProcedure }) {
  const name = cp.custom_name_ko || cp.procedure?.name_ko || "-";
  const duration =
    cp.custom_duration_minutes || cp.procedure?.duration_minutes;
  const pain = cp.procedure?.pain_level;
  const score = cp.sales_performance_score;

  return (
    <div className="flex items-center justify-between border-b px-4 py-3 last:border-b-0 hover:bg-muted/50">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{name}</p>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          {duration && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {duration}분
            </span>
          )}
          {pain !== null && pain !== undefined && (
            <span>통증 {pain}/10</span>
          )}
          {cp.procedure?.downtime_days !== null &&
            cp.procedure?.downtime_days !== undefined && (
              <span>다운타임 {cp.procedure.downtime_days}일</span>
            )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {score !== null && score !== undefined && (
          <div className="flex items-center gap-1 text-sm">
            <Star className="h-3.5 w-3.5 text-yellow-500" />
            <span className="font-medium">{score}</span>
          </div>
        )}
        {!cp.is_active && (
          <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700">
            비활성
          </span>
        )}
      </div>
    </div>
  );
}

export default function ProceduresPage() {
  const { accessToken } = useAuthStore();
  const {
    categories,
    clinicProcedures,
    procedures,
    fetchCategories,
    fetchProcedures,
    fetchClinicProcedures,
  } = useProcedureStore();

  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(
    null,
  );
  const [viewMode, setViewMode] = useState<"clinic" | "base">("clinic");

  useEffect(() => {
    if (accessToken) {
      fetchCategories(accessToken);
      fetchClinicProcedures(accessToken);
      fetchProcedures(accessToken);
    }
  }, [accessToken, fetchCategories, fetchClinicProcedures, fetchProcedures]);

  const filteredClinicProcedures = selectedCategoryId
    ? clinicProcedures.filter(
        (cp) => cp.procedure?.category_id === selectedCategoryId,
      )
    : clinicProcedures;

  const filteredProcedures = selectedCategoryId
    ? procedures.filter((p) => p.category_id === selectedCategoryId)
    : procedures;

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Category Tree - Left */}
      <div className="flex w-[220px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">카테고리</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <button
            onClick={() => setSelectedCategoryId(null)}
            className={`mb-1 flex w-full items-center rounded px-2 py-1.5 text-sm transition-colors ${
              selectedCategoryId === null
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            전체
          </button>
          {categories.map((cat) => (
            <CategoryItem
              key={cat.id}
              category={cat}
              selectedId={selectedCategoryId}
              onSelect={setSelectedCategoryId}
            />
          ))}
        </div>
      </div>

      {/* Procedure List - Right */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <Syringe className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">시술 관리</h2>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex rounded-lg border">
              <button
                onClick={() => setViewMode("clinic")}
                className={`px-3 py-1 text-xs transition-colors ${
                  viewMode === "clinic"
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                내 클리닉
              </button>
              <button
                onClick={() => setViewMode("base")}
                className={`px-3 py-1 text-xs transition-colors ${
                  viewMode === "base"
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                기본 시술
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {viewMode === "clinic" ? (
            filteredClinicProcedures.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                <Syringe className="mb-2 h-8 w-8" />
                <p className="text-sm">등록된 시술이 없습니다</p>
                <p className="mt-1 text-xs">
                  기본 시술 탭에서 시술을 추가하세요
                </p>
              </div>
            ) : (
              filteredClinicProcedures.map((cp) => (
                <ProcedureRow key={cp.id} cp={cp} />
              ))
            )
          ) : filteredProcedures.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
              <Syringe className="mb-2 h-8 w-8" />
              <p className="text-sm">기본 시술이 없습니다</p>
            </div>
          ) : (
            filteredProcedures.map((proc) => (
              <div
                key={proc.id}
                className="flex items-center justify-between border-b px-4 py-3 hover:bg-muted/50"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{proc.name_ko}</p>
                  <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                    {proc.duration_minutes && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {proc.duration_minutes}분
                      </span>
                    )}
                    {proc.pain_level !== null && (
                      <span>통증 {proc.pain_level}/10</span>
                    )}
                    {proc.slug && (
                      <span className="text-[10px] text-muted-foreground/50">
                        {proc.slug}
                      </span>
                    )}
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    // Add to clinic procedures would go here
                  }}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  추가
                </Button>
              </div>
            ))
          )}
        </div>

        {/* Summary */}
        <div className="border-t px-4 py-2 text-xs text-muted-foreground">
          {viewMode === "clinic"
            ? `클리닉 시술 ${filteredClinicProcedures.length}건`
            : `기본 시술 ${filteredProcedures.length}건`}
        </div>
      </div>
    </div>
  );
}
