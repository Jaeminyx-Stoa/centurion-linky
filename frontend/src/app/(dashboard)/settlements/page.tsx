"use client";

import { useEffect, useState } from "react";
import {
  Receipt,
  CheckCircle,
  Clock,
  Banknote,
  AlertCircle,
  Plus,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useSettlementStore } from "@/stores/settlement";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Settlement } from "@/types/settlement";

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: React.ElementType }
> = {
  pending: { label: "대기", color: "text-yellow-600 bg-yellow-50", icon: Clock },
  confirmed: {
    label: "확인됨",
    color: "text-blue-600 bg-blue-50",
    icon: CheckCircle,
  },
  paid: {
    label: "입금완료",
    color: "text-green-600 bg-green-50",
    icon: Banknote,
  },
};

function formatKRW(amount: number): string {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(amount);
}

function SettlementRow({
  settlement,
  onSelect,
  isSelected,
}: {
  settlement: Settlement;
  onSelect: () => void;
  isSelected: boolean;
}) {
  const config = STATUS_CONFIG[settlement.status] || STATUS_CONFIG.pending;
  const StatusIcon = config.icon;

  return (
    <button
      onClick={onSelect}
      className={`flex w-full items-center gap-4 border-b px-4 py-3 text-left transition-colors ${
        isSelected ? "bg-muted" : "hover:bg-muted/50"
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {settlement.period_year}년 {settlement.period_month}월
          </span>
          <span
            className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium ${config.color}`}
          >
            <StatusIcon className="h-3 w-3" />
            {config.label}
          </span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          <span>결제 {settlement.total_payment_count}건</span>
          <span>수수료율 {settlement.commission_rate}%</span>
        </div>
      </div>
      <div className="text-right">
        <p className="text-sm font-bold">
          {formatKRW(settlement.total_settlement)}
        </p>
        <p className="text-xs text-muted-foreground">정산금</p>
      </div>
    </button>
  );
}

function SettlementDetail({
  settlement,
  onConfirm,
  onMarkPaid,
}: {
  settlement: Settlement;
  onConfirm: () => void;
  onMarkPaid: () => void;
}) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {settlement.period_year}년 {settlement.period_month}월 정산 상세
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between border-b pb-2">
              <span className="text-sm text-muted-foreground">총 결제액</span>
              <span className="text-sm font-medium">
                {formatKRW(settlement.total_payment_amount)}
              </span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-sm text-muted-foreground">
                수수료 ({settlement.commission_rate}%)
              </span>
              <span className="text-sm font-medium">
                {formatKRW(settlement.commission_amount)}
              </span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-sm text-muted-foreground">
                부가세 (10%)
              </span>
              <span className="text-sm font-medium">
                {formatKRW(settlement.vat_amount)}
              </span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-sm font-bold">정산 합계</span>
              <span className="text-base font-bold text-primary">
                {formatKRW(settlement.total_settlement)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-0">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">결제 건수</span>
              <span>{settlement.total_payment_count}건</span>
            </div>
            {settlement.confirmed_at && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">확인 일시</span>
                <span>
                  {new Date(settlement.confirmed_at).toLocaleString("ko")}
                </span>
              </div>
            )}
            {settlement.paid_at && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">입금 일시</span>
                <span>
                  {new Date(settlement.paid_at).toLocaleString("ko")}
                </span>
              </div>
            )}
            {settlement.notes && (
              <div className="mt-2 rounded bg-muted p-2 text-sm">
                {settlement.notes}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        {settlement.status === "pending" && (
          <Button onClick={onConfirm} className="flex-1">
            <CheckCircle className="mr-1 h-4 w-4" />
            정산 확인
          </Button>
        )}
        {settlement.status === "confirmed" && (
          <Button onClick={onMarkPaid} className="flex-1">
            <Banknote className="mr-1 h-4 w-4" />
            입금 확인
          </Button>
        )}
      </div>
    </div>
  );
}

export default function SettlementsPage() {
  const { accessToken } = useAuthStore();
  const {
    settlements,
    selectedSettlement,
    isLoading,
    error,
    fetchSettlements,
    selectSettlement,
    generateSettlement,
    confirmSettlement,
    markPaid,
  } = useSettlementStore();

  const [filterYear, setFilterYear] = useState<number>(
    new Date().getFullYear(),
  );

  useEffect(() => {
    if (accessToken) {
      fetchSettlements(accessToken, filterYear);
    }
  }, [accessToken, filterYear, fetchSettlements]);

  const handleGenerate = () => {
    if (!accessToken) return;
    const now = new Date();
    const prevMonth = now.getMonth() === 0 ? 12 : now.getMonth();
    const prevYear =
      now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
    generateSettlement(accessToken, { year: prevYear, month: prevMonth });
  };

  const handleConfirm = () => {
    if (accessToken && selectedSettlement) {
      confirmSettlement(accessToken, selectedSettlement.id);
    }
  };

  const handleMarkPaid = () => {
    if (accessToken && selectedSettlement) {
      markPaid(accessToken, selectedSettlement.id);
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left: Settlement List */}
      <div className="flex w-[360px] flex-col border-r">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold">정산 관리</h2>
            <p className="text-xs text-muted-foreground">
              {settlements.length}건
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={filterYear}
              onChange={(e) => setFilterYear(Number(e.target.value))}
              className="rounded border px-2 py-1 text-xs"
            >
              {[2024, 2025, 2026].map((y) => (
                <option key={y} value={y}>
                  {y}년
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={handleGenerate}
            >
              <Plus className="mr-1 h-3 w-3" />
              생성
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center p-8 text-muted-foreground">
              <Receipt className="mr-2 h-5 w-5 animate-pulse" />
              로딩 중...
            </div>
          ) : settlements.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
              <Receipt className="mb-2 h-8 w-8" />
              <p className="text-sm">정산 내역이 없습니다</p>
            </div>
          ) : (
            settlements.map((s) => (
              <SettlementRow
                key={s.id}
                settlement={s}
                isSelected={selectedSettlement?.id === s.id}
                onSelect={() => {
                  if (accessToken) selectSettlement(accessToken, s.id);
                }}
              />
            ))
          )}
        </div>
      </div>

      {/* Right: Settlement Detail */}
      <div className="flex flex-1 flex-col overflow-y-auto p-6">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        {selectedSettlement ? (
          <SettlementDetail
            settlement={selectedSettlement}
            onConfirm={handleConfirm}
            onMarkPaid={handleMarkPaid}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            <p className="text-sm">정산을 선택하세요</p>
          </div>
        )}
      </div>
    </div>
  );
}

