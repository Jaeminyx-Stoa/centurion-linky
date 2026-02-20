"use client";

import { useEffect, useState } from "react";
import {
  FlaskConical,
  AlertCircle,
  Plus,
  Play,
  BarChart3,
  Bot,
  CheckCircle,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useAILabStore } from "@/stores/ai-lab";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type TabId = "ab-tests" | "simulations";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "ab-tests", label: "A/B 테스트", icon: BarChart3 },
  { id: "simulations", label: "AI 시뮬레이션", icon: Bot },
];

const TEST_STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-500",
  active: "bg-green-50 text-green-700",
  paused: "bg-yellow-50 text-yellow-700",
  completed: "bg-blue-50 text-blue-700",
};

function ABTestsTab() {
  const { accessToken } = useAuthStore();
  const { abTests, abTestStats, createABTest, updateABTest, fetchABTestStats } =
    useAILabStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [testType, setTestType] = useState("persona");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!accessToken || !name.trim()) return;
    await createABTest(accessToken, {
      name: name.trim(),
      description: description.trim() || undefined,
      test_type: testType,
      variants: [
        { name: "Control", config: {} },
        { name: "Variant A", config: {} },
      ],
    });
    setName("");
    setDescription("");
    setShowCreate(false);
  };

  const handleToggleStatus = async (testId: string, currentStatus: string) => {
    if (!accessToken) return;
    const newStatus = currentStatus === "active" ? "paused" : "active";
    await updateABTest(accessToken, testId, { status: newStatus });
  };

  const handleExpand = async (testId: string) => {
    if (expandedId === testId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(testId);
    if (accessToken && !abTestStats[testId]) {
      await fetchABTestStats(accessToken, testId);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">A/B 테스트</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          새 테스트
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label htmlFor="ab-name">테스트 이름</Label>
              <Input
                id="ab-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="예: 페르소나 비교 테스트"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ab-desc">설명 (선택)</Label>
              <Input
                id="ab-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="테스트 설명"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ab-type">테스트 유형</Label>
              <select
                id="ab-type"
                value={testType}
                onChange={(e) => setTestType(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm"
              >
                <option value="persona">페르소나</option>
                <option value="prompt">프롬프트</option>
                <option value="strategy">전략</option>
              </select>
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

      {abTests.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
          <BarChart3 className="mb-2 h-8 w-8" />
          <p className="text-sm">A/B 테스트가 없습니다</p>
        </div>
      ) : (
        <div className="space-y-3">
          {abTests.map((test) => (
            <Card key={test.id}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{test.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {test.test_type} | {test.variants.length}개 변형
                      {test.description && ` | ${test.description}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        TEST_STATUS_COLORS[test.status] ||
                        "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {test.status}
                    </span>
                    {(test.status === "active" ||
                      test.status === "paused" ||
                      test.status === "draft") && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() =>
                          handleToggleStatus(test.id, test.status)
                        }
                      >
                        {test.status === "active" ? "일시정지" : "시작"}
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={() => handleExpand(test.id)}
                    >
                      통계
                    </Button>
                  </div>
                </div>

                {/* Variants */}
                <div className="mt-3 flex gap-2">
                  {test.variants.map((v) => (
                    <span
                      key={v.id}
                      className="rounded bg-muted px-2 py-1 text-xs"
                    >
                      {v.name} (w:{v.weight})
                    </span>
                  ))}
                </div>

                {/* Stats */}
                {expandedId === test.id && abTestStats[test.id] && (
                  <div className="mt-3 space-y-2 rounded border p-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      결과 통계
                    </p>
                    {abTestStats[test.id].map((stat) => (
                      <div
                        key={stat.variant_id}
                        className="flex items-center justify-between text-sm"
                      >
                        <span>{stat.variant_name}</span>
                        <span>
                          {stat.total_conversations}건 |{" "}
                          {stat.positive_outcomes}성공 |{" "}
                          {(stat.conversion_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function SimulationsTab() {
  const { accessToken } = useAuthStore();
  const {
    simulations,
    personas,
    createSimulation,
    completeSimulation,
  } = useAILabStore();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState("");
  const [maxRounds, setMaxRounds] = useState("10");

  const handleCreate = async () => {
    if (!accessToken || !selectedPersona) return;
    await createSimulation(accessToken, {
      persona_name: selectedPersona,
      max_rounds: Number(maxRounds) || 10,
    });
    setSelectedPersona("");
    setShowCreate(false);
  };

  const handleComplete = async (id: string) => {
    if (!accessToken) return;
    await completeSimulation(accessToken, id);
  };

  const SIM_STATUS_COLORS: Record<string, string> = {
    pending: "bg-yellow-50 text-yellow-700",
    running: "bg-blue-50 text-blue-700",
    completed: "bg-green-50 text-green-700",
    failed: "bg-red-50 text-red-700",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">AI 시뮬레이션</h2>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="mr-1 h-3 w-3" />
          새 시뮬레이션
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="space-y-2">
              <Label htmlFor="sim-persona">페르소나 선택</Label>
              <select
                id="sim-persona"
                value={selectedPersona}
                onChange={(e) => setSelectedPersona(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm"
              >
                <option value="">선택하세요</option>
                {personas.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name} ({p.country}/{p.language})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="sim-rounds">최대 라운드</Label>
              <Input
                id="sim-rounds"
                type="number"
                value={maxRounds}
                onChange={(e) => setMaxRounds(e.target.value)}
                placeholder="10"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate}>
                <Play className="mr-1 h-3 w-3" />
                시작
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

      {/* Persona Gallery */}
      {personas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">사용 가능한 페르소나</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-2">
              {personas.map((p) => (
                <div
                  key={p.name}
                  className="rounded border p-2 text-xs"
                >
                  <p className="font-medium">{p.name}</p>
                  <p className="text-muted-foreground">
                    {p.country} | {p.language}
                  </p>
                  <p className="mt-1 truncate text-muted-foreground">
                    {p.behavior}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Simulation List */}
      {simulations.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
          <Bot className="mb-2 h-8 w-8" />
          <p className="text-sm">시뮬레이션이 없습니다</p>
        </div>
      ) : (
        <div className="space-y-3">
          {simulations.map((sim) => (
            <Card key={sim.id}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{sim.persona_name}</p>
                    <p className="text-xs text-muted-foreground">
                      라운드: {sim.actual_rounds}/{sim.max_rounds}
                      {sim.started_at &&
                        ` | 시작: ${new Date(sim.started_at).toLocaleString("ko-KR")}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        SIM_STATUS_COLORS[sim.status] ||
                        "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {sim.status}
                    </span>
                    {(sim.status === "running" ||
                      sim.status === "pending") && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => handleComplete(sim.id)}
                      >
                        <CheckCircle className="mr-1 h-3 w-3" />
                        완료
                      </Button>
                    )}
                  </div>
                </div>

                {/* Result */}
                {sim.result && (
                  <div className="mt-3 rounded border p-3">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      결과
                    </p>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground">예약: </span>
                        <span
                          className={
                            sim.result.booked
                              ? "text-green-600"
                              : "text-red-600"
                          }
                        >
                          {sim.result.booked ? "성공" : "실패"}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">결제: </span>
                        <span
                          className={
                            sim.result.paid
                              ? "text-green-600"
                              : "text-red-600"
                          }
                        >
                          {sim.result.paid ? "성공" : "실패"}
                        </span>
                      </div>
                      {sim.result.satisfaction_score != null && (
                        <div>
                          <span className="text-muted-foreground">
                            만족도:{" "}
                          </span>
                          <span>{sim.result.satisfaction_score}/5</span>
                        </div>
                      )}
                      {sim.result.exit_reason && (
                        <div>
                          <span className="text-muted-foreground">
                            종료 사유:{" "}
                          </span>
                          <span>{sim.result.exit_reason}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AILabPage() {
  const { accessToken } = useAuthStore();
  const { isLoading, error, fetchAll } = useAILabStore();
  const [activeTab, setActiveTab] = useState<TabId>("ab-tests");

  useEffect(() => {
    if (accessToken) {
      fetchAll(accessToken);
    }
  }, [accessToken, fetchAll]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <FlaskConical className="mr-2 h-5 w-5 animate-pulse" />
        AI Lab 로딩 중...
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
      {/* Tab sidebar (desktop) */}
      <div className="hidden md:flex w-[180px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">AI Lab</h2>
        </div>
        <nav className="flex-1 p-2" aria-label="AI Lab 탭">
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
      <div className="flex overflow-x-auto border-b md:hidden" role="tablist" aria-label="AI Lab 탭">
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
      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        {activeTab === "ab-tests" && <ABTestsTab />}
        {activeTab === "simulations" && <SimulationsTab />}
      </div>
    </div>
  );
}
