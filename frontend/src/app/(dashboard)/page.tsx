"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth";

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">대시보드</h2>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>활성 대화</CardTitle>
            <CardDescription>진행 중인 상담</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">0</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>오늘 예약</CardTitle>
            <CardDescription>금일 예정된 시술</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">0</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>AI 응답률</CardTitle>
            <CardDescription>자동 응답 비율</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">-</p>
          </CardContent>
        </Card>
      </div>
      {user && (
        <p className="text-sm text-muted-foreground">
          {user.name}님, 환영합니다.
        </p>
      )}
    </div>
  );
}
