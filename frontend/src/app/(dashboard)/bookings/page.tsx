"use client";

import { useEffect, useState } from "react";
import {
  Calendar,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Ban,
  UserX,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useBookingStore } from "@/stores/booking";
import { Button } from "@/components/ui/button";
import { ListSkeleton } from "@/components/shared/skeletons";
import { PaginationControls } from "@/components/shared/pagination-controls";
import type { BookingStatus } from "@/types/booking";
import {
  BOOKING_STATUS_LABELS,
  BOOKING_STATUS_COLORS,
} from "@/types/booking";

const STATUS_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "전체" },
  { id: "pending", label: "대기" },
  { id: "confirmed", label: "확정" },
  { id: "completed", label: "완료" },
  { id: "cancelled", label: "취소" },
  { id: "no_show", label: "노쇼" },
];

const STATUS_ICONS: Record<string, React.ElementType> = {
  pending: Clock,
  confirmed: CheckCircle,
  completed: CheckCircle,
  cancelled: XCircle,
  no_show: UserX,
};

export default function BookingsPage() {
  const { accessToken } = useAuthStore();
  const {
    bookings, isLoading, error, total, page, pageSize,
    fetchBookings, setPage, cancelBooking, completeBooking,
  } = useBookingStore();
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    if (accessToken) {
      fetchBookings(accessToken, statusFilter === "all" ? undefined : statusFilter);
    }
  }, [accessToken, fetchBookings, statusFilter, page]);

  const handleCancel = async (id: string) => {
    if (!accessToken) return;
    await cancelBooking(accessToken, id);
  };

  const handleComplete = async (id: string) => {
    if (!accessToken) return;
    await completeBooking(accessToken, id);
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <h1 className="text-lg font-bold">예약 관리</h1>
          </div>
          <span className="text-sm text-muted-foreground">
            총 {total}건
          </span>
        </div>
        {/* Status Filters */}
        <div className="mt-3 flex gap-2 overflow-x-auto">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => { setStatusFilter(f.id); setPage(1); }}
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
      </div>

      {error && (
        <div className="mx-6 mt-4 flex items-center gap-2 rounded bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <ListSkeleton />
        ) : bookings.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
            <Calendar className="mb-2 h-8 w-8" />
            <p className="text-sm">예약이 없습니다</p>
          </div>
        ) : (
          <div className="divide-y">
            {bookings.map((booking) => {
              const StatusIcon =
                STATUS_ICONS[booking.status] || AlertCircle;
              return (
                <div
                  key={booking.id}
                  className="flex flex-col gap-2 px-6 py-4 hover:bg-muted/50 md:flex-row md:items-center md:justify-between"
                >
                  <div className="flex items-center gap-4">
                    <StatusIcon className="h-5 w-5 shrink-0 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">
                        {booking.booking_date} {booking.booking_time}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {booking.customer_id.slice(0, 8)}...
                        {booking.total_amount != null &&
                          ` | ${booking.total_amount.toLocaleString()} ${booking.currency}`}
                      </p>
                      {booking.notes && (
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {booking.notes}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        BOOKING_STATUS_COLORS[booking.status as BookingStatus] ||
                        "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {BOOKING_STATUS_LABELS[booking.status as BookingStatus] ||
                        booking.status}
                    </span>
                    {booking.status === "confirmed" && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => handleComplete(booking.id)}
                        aria-label="예약 완료"
                      >
                        <CheckCircle className="mr-1 h-3 w-3" />
                        완료
                      </Button>
                    )}
                    {(booking.status === "pending" ||
                      booking.status === "confirmed") && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs text-destructive hover:text-destructive"
                        onClick={() => handleCancel(booking.id)}
                        aria-label="예약 취소"
                      >
                        <Ban className="mr-1 h-3 w-3" />
                        취소
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
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
