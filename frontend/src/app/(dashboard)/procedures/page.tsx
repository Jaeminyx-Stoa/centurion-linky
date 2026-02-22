"use client";

import { useEffect, useState } from "react";
import {
  Syringe,
  ChevronRight,
  Plus,
  Clock,
  Star,
  DollarSign,
  FolderTree,
  Trash2,
  Save,
  Package,
  ClipboardCheck,
  HeartPulse,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useProcedureStore } from "@/stores/procedure";
import { usePackageStore } from "@/stores/package";
import { useProtocolStore } from "@/stores/protocol";
import { useFollowupStore } from "@/stores/followup";
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
import type { ProcedureCategoryTree, ClinicProcedure } from "@/types/procedure";

type TabId = "clinic" | "categories" | "pricing" | "packages" | "protocols" | "followups";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "clinic", label: "시술 목록", icon: Syringe },
  { id: "categories", label: "카테고리", icon: FolderTree },
  { id: "pricing", label: "가격 관리", icon: DollarSign },
  { id: "packages", label: "패키지", icon: Package },
  { id: "protocols", label: "상담 프로토콜", icon: ClipboardCheck },
  { id: "followups", label: "시술 후 관리", icon: HeartPulse },
];

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

function ClinicTab() {
  const { accessToken } = useAuthStore();
  const {
    categories,
    clinicProcedures,
    procedures,
    fetchCategories,
    fetchProcedures,
    fetchClinicProcedures,
    addClinicProcedure,
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

  const handleAdd = async (procedureId: string) => {
    if (!accessToken) return;
    await addClinicProcedure(accessToken, { procedure_id: procedureId });
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Category Tree */}
      <div className="flex w-[200px] flex-col border-r">
        <div className="border-b px-3 py-2">
          <h3 className="text-xs font-semibold text-muted-foreground">
            카테고리
          </h3>
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

      {/* List */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b px-4 py-2">
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
        <div className="flex-1 overflow-y-auto">
          {viewMode === "clinic" ? (
            filteredClinicProcedures.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                <Syringe className="mb-2 h-8 w-8" />
                <p className="text-sm">등록된 시술이 없습니다</p>
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
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => handleAdd(proc.id)}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  추가
                </Button>
              </div>
            ))
          )}
        </div>
        <div className="border-t px-4 py-2 text-xs text-muted-foreground">
          {viewMode === "clinic"
            ? `클리닉 시술 ${filteredClinicProcedures.length}건`
            : `기본 시술 ${filteredProcedures.length}건`}
        </div>
      </div>
    </div>
  );
}

function CategoriesTab() {
  const { accessToken } = useAuthStore();
  const { categories, createCategory } = useProcedureStore();
  const [showCreate, setShowCreate] = useState(false);
  const [nameKo, setNameKo] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [slug, setSlug] = useState("");

  useEffect(() => {
    if (accessToken) {
      useProcedureStore.getState().fetchCategories(accessToken);
    }
  }, [accessToken]);

  const handleCreate = async () => {
    if (!accessToken || !nameKo.trim() || !slug.trim()) return;
    await createCategory(accessToken, {
      name_ko: nameKo.trim(),
      name_en: nameEn.trim() || undefined,
      slug: slug.trim(),
    });
    setNameKo("");
    setNameEn("");
    setSlug("");
    setShowCreate(false);
  };

  const flattenCategories = (
    cats: ProcedureCategoryTree[],
    depth = 0,
  ): { cat: ProcedureCategoryTree; depth: number }[] => {
    const result: { cat: ProcedureCategoryTree; depth: number }[] = [];
    for (const cat of cats) {
      result.push({ cat, depth });
      result.push(...flattenCategories(cat.children, depth + 1));
    }
    return result;
  };

  const flatCats = flattenCategories(categories);

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">카테고리 관리</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          추가
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label htmlFor="cat-name-ko">이름 (한국어)</Label>
              <Input
                id="cat-name-ko"
                value={nameKo}
                onChange={(e) => setNameKo(e.target.value)}
                placeholder="예: 피부 시술"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat-name-en">이름 (영어)</Label>
              <Input
                id="cat-name-en"
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                placeholder="예: Skin Procedures"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat-slug">슬러그</Label>
              <Input
                id="cat-slug"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="예: skin-procedures"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate}>
                생성
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreate(false)}
              >
                취소
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {flatCats.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              카테고리가 없습니다
            </p>
          ) : (
            <div className="divide-y">
              {flatCats.map(({ cat, depth }) => (
                <div
                  key={cat.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                  style={{ paddingLeft: `${depth * 24 + 16}px` }}
                >
                  <div>
                    <p className="text-sm font-medium">{cat.name_ko}</p>
                    <p className="text-xs text-muted-foreground">
                      {cat.slug}
                      {cat.name_en && ` | ${cat.name_en}`}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    #{cat.sort_order}
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

function PricingTab() {
  const { accessToken } = useAuthStore();
  const {
    pricings,
    clinicProcedures,
    fetchPricings,
    fetchClinicProcedures,
    createPricing,
    deletePricing,
  } = useProcedureStore();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedCpId, setSelectedCpId] = useState("");
  const [regularPrice, setRegularPrice] = useState("");
  const [eventPrice, setEventPrice] = useState("");

  useEffect(() => {
    if (accessToken) {
      fetchPricings(accessToken);
      fetchClinicProcedures(accessToken);
    }
  }, [accessToken, fetchPricings, fetchClinicProcedures]);

  const handleCreate = async () => {
    if (!accessToken || !selectedCpId || !regularPrice) return;
    await createPricing(accessToken, {
      clinic_procedure_id: selectedCpId,
      regular_price: Number(regularPrice),
      event_price: eventPrice ? Number(eventPrice) : undefined,
    });
    setSelectedCpId("");
    setRegularPrice("");
    setEventPrice("");
    setShowCreate(false);
  };

  const handleDelete = async (id: string) => {
    if (!accessToken) return;
    await deletePricing(accessToken, id);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">가격 관리</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          추가
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label htmlFor="price-cp">시술 선택</Label>
              <select
                id="price-cp"
                value={selectedCpId}
                onChange={(e) => setSelectedCpId(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm"
              >
                <option value="">선택하세요</option>
                {clinicProcedures.map((cp) => (
                  <option key={cp.id} value={cp.id}>
                    {cp.custom_name_ko || cp.procedure?.name_ko || cp.id}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="price-regular">정가</Label>
              <Input
                id="price-regular"
                type="number"
                value={regularPrice}
                onChange={(e) => setRegularPrice(e.target.value)}
                placeholder="500000"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price-event">이벤트 가격 (선택)</Label>
              <Input
                id="price-event"
                type="number"
                value={eventPrice}
                onChange={(e) => setEventPrice(e.target.value)}
                placeholder="400000"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate}>
                생성
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreate(false)}
              >
                취소
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {pricings.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              등록된 가격이 없습니다
            </p>
          ) : (
            <div className="divide-y">
              {pricings.map((pricing) => {
                const cp = clinicProcedures.find(
                  (c) => c.id === pricing.clinic_procedure_id,
                );
                return (
                  <div
                    key={pricing.id}
                    className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {cp?.custom_name_ko ||
                          cp?.procedure?.name_ko ||
                          pricing.clinic_procedure_id.slice(0, 8)}
                      </p>
                      <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                        <span>
                          정가: {pricing.regular_price.toLocaleString()}원
                        </span>
                        {pricing.event_price != null && (
                          <span className="text-green-600">
                            이벤트: {pricing.event_price.toLocaleString()}원
                          </span>
                        )}
                        {pricing.discount_rate != null && (
                          <span>할인: {pricing.discount_rate}%</span>
                        )}
                        {pricing.is_package && (
                          <span className="rounded bg-blue-50 px-1 text-blue-600">
                            패키지
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!pricing.is_active && (
                        <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700">
                          비활성
                        </span>
                      )}
                      {pricing.discount_warning && (
                        <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-[10px] text-yellow-700">
                          할인경고
                        </span>
                      )}
                      <button
                        onClick={() => handleDelete(pricing.id)}
                        className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                        aria-label="가격 삭제"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ProtocolsTab() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const { protocols, fetchProtocols, createProtocol } = useProtocolStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [itemQuestion, setItemQuestion] = useState("");
  const [items, setItems] = useState<
    { id: string; question_ko: string; required: boolean; type: string }[]
  >([]);

  useEffect(() => {
    if (accessToken) {
      fetchProtocols(accessToken);
    }
  }, [accessToken, fetchProtocols]);

  const handleAddItem = () => {
    if (!itemQuestion.trim()) return;
    setItems([
      ...items,
      {
        id: `chk_${items.length + 1}`,
        question_ko: itemQuestion.trim(),
        required: true,
        type: "boolean",
      },
    ]);
    setItemQuestion("");
  };

  const handleCreate = async () => {
    if (!accessToken || !name.trim() || items.length === 0) return;
    await createProtocol(accessToken, {
      name: name.trim(),
      checklist_items: items,
    });
    setName("");
    setItems([]);
    setShowCreate(false);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">{t("protocols.title")}</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          {t("protocols.create")}
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label htmlFor="proto-name">{t("protocols.name")}</Label>
              <Input
                id="proto-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="예: 보톡스 상담 프로토콜"
              />
            </div>
            <div className="space-y-2">
              <Label>{t("protocols.items")} ({items.length})</Label>
              {items.map((item, idx) => (
                <div
                  key={item.id}
                  className="flex items-center gap-2 rounded border px-2 py-1 text-xs"
                >
                  <span className="text-muted-foreground">{item.id}</span>
                  <span className="flex-1">{item.question_ko}</span>
                  <button
                    onClick={() =>
                      setItems(items.filter((_, i) => i !== idx))
                    }
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
              <div className="flex gap-1">
                <Input
                  value={itemQuestion}
                  onChange={(e) => setItemQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddItem()}
                  className="h-7 text-xs"
                  placeholder={t("protocols.question")}
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 px-2"
                  onClick={handleAddItem}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate}>
                {t("common.save")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreate(false)}
              >
                {t("common.cancel")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {protocols.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              {t("protocols.empty")}
            </p>
          ) : (
            <div className="divide-y">
              {protocols.map((proto) => {
                const itemCount = proto.checklist_items?.length || 0;
                return (
                  <div
                    key={proto.id}
                    className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                  >
                    <div>
                      <p className="text-sm font-medium">{proto.name}</p>
                      <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                        <span>
                          {t("protocols.itemCount")}: {itemCount}
                        </span>
                        <span>
                          {proto.procedure_id
                            ? t("protocols.procedure")
                            : t("protocols.global")}
                        </span>
                      </div>
                    </div>
                    {!proto.is_active && (
                      <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700">
                        비활성
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PackagesTab() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const { packages, isLoading, fetchPackages, createPackage } =
    usePackageStore();
  const [showCreate, setShowCreate] = useState(false);
  const [nameKo, setNameKo] = useState("");
  const [price, setPrice] = useState("");
  const [totalSessions, setTotalSessions] = useState("1");
  const [discount, setDiscount] = useState("");

  useEffect(() => {
    if (accessToken) {
      fetchPackages(accessToken);
    }
  }, [accessToken, fetchPackages]);

  const handleCreate = async () => {
    if (!accessToken || !nameKo.trim()) return;
    await createPackage(accessToken, {
      name_ko: nameKo.trim(),
      total_sessions: Number(totalSessions) || 1,
      package_price: price ? Number(price) : undefined,
      discount_rate: discount ? Number(discount) : undefined,
    } as never);
    setNameKo("");
    setPrice("");
    setTotalSessions("1");
    setDiscount("");
    setShowCreate(false);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">{t("packages.title")}</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          {t("packages.create")}
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label htmlFor="pkg-name">{t("packages.name")}</Label>
              <Input
                id="pkg-name"
                value={nameKo}
                onChange={(e) => setNameKo(e.target.value)}
                placeholder="예: 보톡스 3회 패키지"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-2">
                <Label htmlFor="pkg-sessions">{t("packages.totalSessions")}</Label>
                <Input
                  id="pkg-sessions"
                  type="number"
                  value={totalSessions}
                  onChange={(e) => setTotalSessions(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pkg-price">{t("packages.price")}</Label>
                <Input
                  id="pkg-price"
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="1500000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pkg-discount">{t("packages.discount")} (%)</Label>
                <Input
                  id="pkg-discount"
                  type="number"
                  value={discount}
                  onChange={(e) => setDiscount(e.target.value)}
                  placeholder="20"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate}>
                {t("common.save")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreate(false)}
              >
                {t("common.cancel")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {packages.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              {t("packages.empty")}
            </p>
          ) : (
            <div className="divide-y">
              {packages.map((pkg) => (
                <div
                  key={pkg.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                >
                  <div>
                    <p className="text-sm font-medium">{pkg.name_ko}</p>
                    <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>
                        {t("packages.totalSessions")}: {pkg.total_sessions}
                      </span>
                      {pkg.package_price != null && (
                        <span>
                          {Number(pkg.package_price).toLocaleString()}원
                        </span>
                      )}
                      {pkg.discount_rate != null && (
                        <span className="text-green-600">
                          {t("packages.discount")}: {Number(pkg.discount_rate)}%
                        </span>
                      )}
                    </div>
                  </div>
                  {!pkg.is_active && (
                    <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700">
                      비활성
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function FollowupsTab() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const { rules, keywords, fetchRules, fetchKeywords, createRule, deleteRule, createKeywords } =
    useFollowupStore();
  const [showCreate, setShowCreate] = useState(false);
  const [eventType, setEventType] = useState("recovery_check");
  const [delayDays, setDelayDays] = useState("1");
  const [delayHours, setDelayHours] = useState("0");
  const [templateKo, setTemplateKo] = useState("");
  const [templateEn, setTemplateEn] = useState("");

  const [showKw, setShowKw] = useState(false);
  const [kwLang, setKwLang] = useState("ko");
  const [kwText, setKwText] = useState("");
  const [kwSeverity, setKwSeverity] = useState("normal");

  useEffect(() => {
    if (accessToken) {
      fetchRules(accessToken);
      fetchKeywords(accessToken);
    }
  }, [accessToken, fetchRules, fetchKeywords]);

  const EVENT_TYPES = [
    { value: "recovery_check", label: t("followups.type.recoveryCheck") },
    { value: "side_effect_check", label: t("followups.type.sideEffectCheck") },
    { value: "result_check", label: t("followups.type.resultCheck") },
    { value: "retouch_reminder", label: t("followups.type.retouchReminder") },
  ];

  const handleCreateRule = async () => {
    if (!accessToken) return;
    const template: Record<string, string> = {};
    if (templateKo.trim()) template.ko = templateKo.trim();
    if (templateEn.trim()) template.en = templateEn.trim();
    await createRule(accessToken, {
      event_type: eventType,
      delay_days: Number(delayDays) || 0,
      delay_hours: Number(delayHours) || 0,
      message_template: Object.keys(template).length > 0 ? template : null,
    });
    setShowCreate(false);
    setTemplateKo("");
    setTemplateEn("");
  };

  const handleCreateKw = async () => {
    if (!accessToken || !kwText.trim()) return;
    const kws = kwText.split(",").map((k) => k.trim()).filter(Boolean);
    await createKeywords(accessToken, {
      language: kwLang,
      keywords: kws,
      severity: kwSeverity,
    });
    setShowKw(false);
    setKwText("");
  };

  return (
    <div className="space-y-4 p-6">
      {/* Rules Section */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">{t("followups.rules")}</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          {t("followups.create")}
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label>{t("followups.eventType")}</Label>
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm"
              >
                {EVENT_TYPES.map((et) => (
                  <option key={et.value} value={et.value}>
                    {et.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>{t("followups.delayDays")}</Label>
                <Input
                  type="number"
                  value={delayDays}
                  onChange={(e) => setDelayDays(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("followups.delayHours")}</Label>
                <Input
                  type="number"
                  value={delayHours}
                  onChange={(e) => setDelayHours(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("followups.messageTemplate")} (KO)</Label>
              <Input
                value={templateKo}
                onChange={(e) => setTemplateKo(e.target.value)}
                placeholder="시술 후 상태는 어떠신가요?"
              />
            </div>
            <div className="space-y-2">
              <Label>{t("followups.messageTemplate")} (EN)</Label>
              <Input
                value={templateEn}
                onChange={(e) => setTemplateEn(e.target.value)}
                placeholder="How are you feeling after the procedure?"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateRule}>
                {t("common.save")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreate(false)}
              >
                {t("common.cancel")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {rules.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              {t("followups.empty")}
            </p>
          ) : (
            <div className="divide-y">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {EVENT_TYPES.find((e) => e.value === rule.event_type)?.label || rule.event_type}
                    </p>
                    <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>
                        {rule.delay_days}{t("followups.delayDays")} {rule.delay_hours > 0 ? `${rule.delay_hours}${t("followups.delayHours")}` : ""}
                      </span>
                      <span>
                        {rule.procedure_name || t("followups.global")}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!rule.is_active && (
                      <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700">
                        비활성
                      </span>
                    )}
                    <button
                      onClick={() => accessToken && deleteRule(accessToken, rule.id)}
                      className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Keywords Section */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">{t("followups.keywords")}</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowKw(!showKw)}
        >
          <Plus className="mr-1 h-3 w-3" />
          {t("followups.create")}
        </Button>
      </div>

      {showKw && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Language</Label>
                <select
                  value={kwLang}
                  onChange={(e) => setKwLang(e.target.value)}
                  className="w-full rounded border px-3 py-2 text-sm"
                >
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                  <option value="ja">日本語</option>
                  <option value="zh">中文</option>
                  <option value="vi">Tiếng Việt</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label>{t("followups.keywordsSeverity")}</Label>
                <select
                  value={kwSeverity}
                  onChange={(e) => setKwSeverity(e.target.value)}
                  className="w-full rounded border px-3 py-2 text-sm"
                >
                  <option value="normal">{t("followups.severity.normal")}</option>
                  <option value="urgent">{t("followups.severity.urgent")}</option>
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("followups.keywords")}</Label>
              <Input
                value={kwText}
                onChange={(e) => setKwText(e.target.value)}
                placeholder="아프다, 부어오르다, 빨갛다, 멍"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateKw}>
                {t("common.save")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowKw(false)}
              >
                {t("common.cancel")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {keywords.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              등록된 키워드가 없습니다
            </p>
          ) : (
            <div className="divide-y">
              {keywords.map((kw) => (
                <div
                  key={kw.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {kw.language.toUpperCase()} — {kw.severity === "urgent" ? t("followups.severity.urgent") : t("followups.severity.normal")}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {kw.keywords.join(", ")}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ProceduresPage() {
  const [activeTab, setActiveTab] = useState<TabId>("clinic");

  return (
    <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
      {/* Tab sidebar (desktop) */}
      <div className="hidden md:flex w-[180px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">시술 관리</h2>
        </div>
        <nav className="flex-1 p-2" aria-label="시술 관리 탭">
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
      <div className="flex overflow-x-auto border-b md:hidden" role="tablist" aria-label="시술 관리 탭">
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
      <div className="flex flex-1 flex-col overflow-hidden">
        {activeTab === "clinic" && <ClinicTab />}
        {activeTab === "categories" && <CategoriesTab />}
        {activeTab === "pricing" && <PricingTab />}
        {activeTab === "packages" && <PackagesTab />}
        {activeTab === "protocols" && <ProtocolsTab />}
        {activeTab === "followups" && <FollowupsTab />}
      </div>
    </div>
  );
}
