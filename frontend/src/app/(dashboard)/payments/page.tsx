"use client";

import { useEffect, useState } from "react";
import {
  CreditCard,
  AlertCircle,
  DollarSign,
  CheckCircle,
  Clock,
  RefreshCcw,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { usePaymentStore } from "@/stores/payment";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { ListSkeleton, CardGridSkeleton } from "@/components/shared/skeletons";
import { PaginationControls } from "@/components/shared/pagination-controls";
import type { PaymentStatus } from "@/types/payment";
import {
  PAYMENT_STATUS_LABELS,
  PAYMENT_STATUS_COLORS,
} from "@/types/payment";

const STATUS_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "전체" },
  { id: "pending", label: "대기" },
  { id: "completed", label: "완료" },
  { id: "failed", label: "실패" },
  { id: "refunded", label: "환불" },
];

function SummaryCard({
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

export default function PaymentsPage() {
  const { accessToken } = useAuthStore();
  const {
    payments, isLoading, error, total, page, pageSize,
    fetchPayments, setPage,
  } = usePaymentStore();
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    if (accessToken) {
      fetchPayments(accessToken);
    }
  }, [accessToken, fetchPayments, page]);

  const filtered =
    statusFilter === "all"
      ? payments
      : payments.filter((p) => p.status === statusFilter);

  const totalAmount = payments
    .filter((p) => p.status === "completed")
    .reduce((sum, p) => sum + p.amount, 0);
  const completedCount = payments.filter(
    (p) => p.status === "completed",
  ).length;
  const pendingCount = payments.filter((p) => p.status === "pending").length;
  const refundedCount = payments.filter((p) => p.status === "refunded").length;

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-bold">결제 관리</h1>
        </div>
        <CardGridSkeleton />
        <ListSkeleton />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-bold">결제 관리</h1>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <SummaryCard
            label="총 결제액"
            value={`${totalAmount.toLocaleString()}`}
            icon={DollarSign}
          />
          <SummaryCard
            label="결제 완료"
            value={completedCount}
            icon={CheckCircle}
            color="text-green-500"
          />
          <SummaryCard
            label="결제 대기"
            value={pendingCount}
            icon={Clock}
            color="text-yellow-500"
          />
          <SummaryCard
            label="환불"
            value={refundedCount}
            icon={RefreshCcw}
            color="text-purple-500"
          />
        </div>

        {/* Filters */}
        <div className="flex gap-2 overflow-x-auto">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => setStatusFilter(f.id)}
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

        {/* Table */}
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
            <CreditCard className="mb-2 h-8 w-8" />
            <p className="text-sm">결제 내역이 없습니다</p>
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {filtered.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">
                          {payment.amount.toLocaleString()} {payment.currency}
                        </p>
                        <span className="text-xs text-muted-foreground">
                          {payment.payment_type}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {payment.pg_provider || "N/A"}
                        {payment.payment_method &&
                          ` | ${payment.payment_method}`}
                        {" | "}
                        {new Date(payment.created_at).toLocaleDateString("ko-KR")}
                      </p>
                    </div>
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        PAYMENT_STATUS_COLORS[
                          payment.status as PaymentStatus
                        ] || "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {PAYMENT_STATUS_LABELS[
                        payment.status as PaymentStatus
                      ] || payment.status}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <PaginationControls
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={setPage}
      />
    </div>
  );
}
