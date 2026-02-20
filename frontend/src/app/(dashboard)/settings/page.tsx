"use client";

import { useEffect, useState } from "react";
import {
  Settings,
  Building2,
  MessageSquare,
  Bot,
  Trash2,
  Plus,
  AlertCircle,
  Save,
  Pencil,
  Copy,
  CreditCard,
  Receipt,
  CheckCircle,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useSettingsStore } from "@/stores/settings";
import type { MessengerAccountUpdate } from "@/types/analytics";
import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type TabId = "clinic" | "messenger" | "persona" | "payment-settings" | "settlements";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "clinic", label: "클리닉 정보", icon: Building2 },
  { id: "messenger", label: "메신저 계정", icon: MessageSquare },
  { id: "persona", label: "AI 페르소나", icon: Bot },
  { id: "payment-settings", label: "결제 설정", icon: CreditCard },
  { id: "settlements", label: "정산 관리", icon: Receipt },
];

const MESSENGER_CONFIGS: Record<
  string,
  { label: string; fields: { key: string; label: string; placeholder?: string }[] }
> = {
  telegram: {
    label: "Telegram",
    fields: [
      { key: "bot_token", label: "Bot Token", placeholder: "123456:ABC-DEF..." },
    ],
  },
  instagram: {
    label: "Instagram",
    fields: [
      { key: "page_access_token", label: "Page Access Token" },
    ],
  },
  facebook: {
    label: "Facebook",
    fields: [
      { key: "page_access_token", label: "Page Access Token" },
    ],
  },
  whatsapp: {
    label: "WhatsApp",
    fields: [
      { key: "access_token", label: "Access Token" },
      { key: "phone_number_id", label: "Phone Number ID" },
    ],
  },
  line: {
    label: "LINE",
    fields: [
      { key: "channel_access_token", label: "Channel Access Token" },
    ],
  },
  kakao: {
    label: "KakaoTalk",
    fields: [
      { key: "api_key", label: "API Key" },
    ],
  },
};

function ClinicTab() {
  const { clinic, updateClinic } = useSettingsStore();
  const { accessToken } = useAuthStore();
  const [name, setName] = useState(clinic?.name || "");
  const [phone, setPhone] = useState(clinic?.phone || "");
  const [address, setAddress] = useState(clinic?.address || "");

  const handleSave = () => {
    if (accessToken) {
      updateClinic(accessToken, { name, phone, address });
    }
  };

  if (!clinic) return null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">기본 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="clinic-name">클리닉명</Label>
              <Input
                id="clinic-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="clinic-slug">슬러그</Label>
              <Input id="clinic-slug" value={clinic.slug} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="clinic-phone">전화번호</Label>
              <Input
                id="clinic-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="clinic-address">주소</Label>
              <Input
                id="clinic-address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>수수료율</Label>
              <p className="text-sm text-muted-foreground">
                {clinic.commission_rate}%
              </p>
            </div>
            <Button onClick={handleSave}>
              <Save className="mr-1 h-4 w-4" />
              저장
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MessengerTab() {
  const {
    messengerAccounts,
    createMessengerAccount,
    updateMessengerAccount,
    deleteMessengerAccount,
  } = useSettingsStore();
  const { accessToken } = useAuthStore();
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Create form state
  const [newType, setNewType] = useState("telegram");
  const [newName, setNewName] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newCredentials, setNewCredentials] = useState<Record<string, string>>(
    {},
  );

  // Edit form state
  const [editName, setEditName] = useState("");
  const [editDisplayName, setEditDisplayName] = useState("");
  const [editIsActive, setEditIsActive] = useState(true);

  const resetCreateForm = () => {
    setNewType("telegram");
    setNewName("");
    setNewDisplayName("");
    setNewCredentials({});
    setShowCreate(false);
  };

  const handleCreate = async () => {
    if (!accessToken || !newName.trim()) return;
    await createMessengerAccount(accessToken, {
      messenger_type: newType,
      account_name: newName.trim(),
      display_name: newDisplayName.trim() || undefined,
      credentials: newCredentials,
    });
    resetCreateForm();
  };

  const startEdit = (account: typeof messengerAccounts[number]) => {
    setEditingId(account.id);
    setEditName(account.account_name);
    setEditDisplayName(account.display_name || "");
    setEditIsActive(account.is_active);
  };

  const handleUpdate = async () => {
    if (!accessToken || !editingId || !editName.trim()) return;
    const data: MessengerAccountUpdate = {
      account_name: editName.trim(),
      display_name: editDisplayName.trim() || undefined,
      is_active: editIsActive,
    };
    await updateMessengerAccount(accessToken, editingId, data);
    setEditingId(null);
  };

  const handleDelete = async (id: string) => {
    if (!accessToken) return;
    await deleteMessengerAccount(accessToken, id);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const currentFields = MESSENGER_CONFIGS[newType]?.fields || [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">연동된 메신저 계정</CardTitle>
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
        </CardHeader>
        <CardContent>
          {showCreate && (
            <div className="mb-4 space-y-3 rounded-lg border p-3">
              <div className="space-y-2">
                <Label>플랫폼</Label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(MESSENGER_CONFIGS).map(([key, cfg]) => (
                    <button
                      key={key}
                      onClick={() => {
                        setNewType(key);
                        setNewCredentials({});
                      }}
                      className={`rounded-md border px-3 py-1.5 text-xs transition-colors ${
                        newType === key
                          ? "border-primary bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }`}
                    >
                      {cfg.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="msg-name">계정 이름</Label>
                <Input
                  id="msg-name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="예: 메인 텔레그램 봇"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="msg-display-name">표시 이름 (선택)</Label>
                <Input
                  id="msg-display-name"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  placeholder="예: Beauty Clinic Bot"
                />
              </div>
              {currentFields.map((field) => (
                <div key={field.key} className="space-y-2">
                  <Label htmlFor={`cred-${field.key}`}>{field.label}</Label>
                  <Input
                    id={`cred-${field.key}`}
                    value={newCredentials[field.key] || ""}
                    onChange={(e) =>
                      setNewCredentials((prev) => ({
                        ...prev,
                        [field.key]: e.target.value,
                      }))
                    }
                    placeholder={field.placeholder}
                  />
                </div>
              ))}
              <div className="flex gap-2">
                <Button size="sm" onClick={handleCreate}>
                  생성
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetCreateForm}
                >
                  취소
                </Button>
              </div>
            </div>
          )}

          {messengerAccounts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              연동된 메신저 계정이 없습니다
            </p>
          ) : (
            <div className="space-y-3">
              {messengerAccounts.map((account) =>
                editingId === account.id ? (
                  <div
                    key={account.id}
                    className="space-y-3 rounded-lg border border-primary/30 p-3"
                  >
                    <div className="space-y-2">
                      <Label htmlFor="edit-name">계정 이름</Label>
                      <Input
                        id="edit-name"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-display-name">표시 이름</Label>
                      <Input
                        id="edit-display-name"
                        value={editDisplayName}
                        onChange={(e) => setEditDisplayName(e.target.value)}
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <Label htmlFor="edit-active">활성</Label>
                      <input
                        id="edit-active"
                        type="checkbox"
                        checked={editIsActive}
                        onChange={(e) => setEditIsActive(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={handleUpdate}>
                        저장
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingId(null)}
                      >
                        취소
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div
                    key={account.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <MessageSquare className="h-5 w-5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">
                          {account.account_name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {MESSENGER_CONFIGS[account.messenger_type]?.label ||
                            account.messenger_type}
                          {account.display_name &&
                            ` — ${account.display_name}`}
                        </p>
                        {account.webhook_url && (
                          <div className="mt-1 flex items-center gap-1">
                            <code className="max-w-[300px] truncate text-[10px] text-muted-foreground">
                              {account.webhook_url}
                            </code>
                            <button
                              onClick={() =>
                                copyToClipboard(account.webhook_url!)
                              }
                              className="rounded p-0.5 hover:bg-muted"
                              title="복사"
                              aria-label="웹훅 URL 복사"
                            >
                              <Copy className="h-3 w-3 text-muted-foreground" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-0.5 text-xs ${
                          account.is_active
                            ? "bg-green-50 text-green-600"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {account.is_active ? "활성" : "비활성"}
                      </span>
                      <button
                        onClick={() => startEdit(account)}
                        className="rounded p-1 text-muted-foreground hover:bg-muted"
                        aria-label="메신저 계정 수정"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(account.id)}
                        className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                        aria-label="메신저 계정 삭제"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PersonaTab() {
  const { aiPersonas, createAIPersona, deleteAIPersona } = useSettingsStore();
  const { accessToken } = useAuthStore();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newPersonality, setNewPersonality] = useState("");

  const handleCreate = async () => {
    if (accessToken && newName.trim()) {
      await createAIPersona(accessToken, {
        name: newName.trim(),
        personality: newPersonality.trim() || undefined,
      });
      setNewName("");
      setNewPersonality("");
      setShowCreate(false);
    }
  };

  const handleDelete = (id: string) => {
    if (accessToken) {
      deleteAIPersona(accessToken, id);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">AI 페르소나</CardTitle>
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
        </CardHeader>
        <CardContent>
          {showCreate && (
            <div className="mb-4 space-y-3 rounded-lg border p-3">
              <div className="space-y-2">
                <Label htmlFor="persona-name">이름</Label>
                <Input
                  id="persona-name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="예: 친절한 상담사"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="persona-personality">성격</Label>
                <Input
                  id="persona-personality"
                  value={newPersonality}
                  onChange={(e) => setNewPersonality(e.target.value)}
                  placeholder="예: 따뜻하고 전문적인"
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
            </div>
          )}

          {aiPersonas.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              AI 페르소나가 없습니다
            </p>
          ) : (
            <div className="space-y-3">
              {aiPersonas.map((persona) => (
                <div
                  key={persona.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <Bot className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">
                        {persona.name}
                        {persona.is_default && (
                          <span className="ml-1 rounded bg-primary/10 px-1 text-[10px] text-primary">
                            기본
                          </span>
                        )}
                      </p>
                      {persona.personality && (
                        <p className="text-xs text-muted-foreground">
                          {persona.personality}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        persona.is_active
                          ? "bg-green-50 text-green-600"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {persona.is_active ? "활성" : "비활성"}
                    </span>
                    {!persona.is_default && (
                      <button
                        onClick={() => handleDelete(persona.id)}
                        className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                        aria-label="AI 페르소나 삭제"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
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

interface PaymentSettings {
  default_provider: string | null;
  default_currency: string | null;
  deposit_required: boolean | null;
  deposit_percentage: number | null;
  payment_expiry_hours: number | null;
}

function PaymentSettingsTab() {
  const { accessToken } = useAuthStore();
  const [settings, setSettings] = useState<PaymentSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState("");
  const [currency, setCurrency] = useState("");
  const [depositRequired, setDepositRequired] = useState(false);
  const [depositPct, setDepositPct] = useState("");
  const [expiryHours, setExpiryHours] = useState("");

  useEffect(() => {
    if (!accessToken) return;
    api
      .get<PaymentSettings>("/api/v1/payment-settings", { token: accessToken })
      .then((data) => {
        setSettings(data);
        setProvider(data.default_provider || "");
        setCurrency(data.default_currency || "KRW");
        setDepositRequired(data.deposit_required || false);
        setDepositPct(String(data.deposit_percentage || ""));
        setExpiryHours(String(data.payment_expiry_hours || ""));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [accessToken]);

  const handleSave = async () => {
    if (!accessToken) return;
    const updated = await api.patch<PaymentSettings>(
      "/api/v1/payment-settings",
      {
        default_provider: provider || null,
        default_currency: currency || null,
        deposit_required: depositRequired,
        deposit_percentage: depositPct ? Number(depositPct) : null,
        payment_expiry_hours: expiryHours ? Number(expiryHours) : null,
      },
      { token: accessToken },
    );
    setSettings(updated);
  };

  if (loading) return <p className="text-sm text-muted-foreground">로딩 중...</p>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">결제 설정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pg-provider">기본 PG사</Label>
            <select
              id="pg-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
            >
              <option value="">선택 안함</option>
              <option value="stripe">Stripe</option>
              <option value="kingorder">KingOrder</option>
              <option value="alipay">Alipay</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="currency">기본 통화</Label>
            <select
              id="currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
            >
              <option value="KRW">KRW</option>
              <option value="USD">USD</option>
              <option value="JPY">JPY</option>
              <option value="CNY">CNY</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="deposit-required">선수금 필수</Label>
            <input
              id="deposit-required"
              type="checkbox"
              checked={depositRequired}
              onChange={(e) => setDepositRequired(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
          </div>
          {depositRequired && (
            <div className="space-y-2">
              <Label htmlFor="deposit-pct">선수금 비율 (%)</Label>
              <Input
                id="deposit-pct"
                type="number"
                value={depositPct}
                onChange={(e) => setDepositPct(e.target.value)}
                placeholder="30"
              />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="expiry-hours">결제 링크 만료 (시간)</Label>
            <Input
              id="expiry-hours"
              type="number"
              value={expiryHours}
              onChange={(e) => setExpiryHours(e.target.value)}
              placeholder="24"
            />
          </div>
          <Button onClick={handleSave}>
            <Save className="mr-1 h-4 w-4" />
            저장
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

interface Settlement {
  id: string;
  clinic_id: string;
  period_year: number;
  period_month: number;
  total_payment_amount: number;
  commission_rate: number;
  commission_amount: number;
  vat_amount: number;
  total_settlement: number;
  total_payment_count: number;
  status: string;
  notes: string | null;
  confirmed_at: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string | null;
}

const SETTLEMENT_STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-500",
  confirmed: "bg-blue-50 text-blue-700",
  paid: "bg-green-50 text-green-700",
};

function SettlementsTab() {
  const { accessToken } = useAuthStore();
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    api
      .get<Settlement[]>("/api/v1/settlements", { token: accessToken })
      .then((data) => {
        setSettlements(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [accessToken]);

  const handleConfirm = async (id: string) => {
    if (!accessToken) return;
    const updated = await api.patch<Settlement>(
      `/api/v1/settlements/${id}/confirm`,
      {},
      { token: accessToken },
    );
    setSettlements((prev) =>
      prev.map((s) => (s.id === id ? updated : s)),
    );
  };

  if (loading) return <p className="text-sm text-muted-foreground">로딩 중...</p>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">정산 목록</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {settlements.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              정산 내역이 없습니다
            </p>
          ) : (
            <div className="divide-y">
              {settlements.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {s.period_year}년 {s.period_month}월
                    </p>
                    <p className="text-xs text-muted-foreground">
                      결제 {s.total_payment_count}건 |{" "}
                      총액 {s.total_payment_amount.toLocaleString()}원 |{" "}
                      수수료 {s.commission_amount.toLocaleString()}원 |{" "}
                      정산 {s.total_settlement.toLocaleString()}원
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        SETTLEMENT_STATUS_COLORS[s.status] ||
                        "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {s.status}
                    </span>
                    {s.status === "draft" && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => handleConfirm(s.id)}
                      >
                        <CheckCircle className="mr-1 h-3 w-3" />
                        확정
                      </Button>
                    )}
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

export default function SettingsPage() {
  const { accessToken } = useAuthStore();
  const { isLoading, error, fetchAll } = useSettingsStore();
  const [activeTab, setActiveTab] = useState<TabId>("clinic");

  useEffect(() => {
    if (accessToken) {
      fetchAll(accessToken);
    }
  }, [accessToken, fetchAll]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <Settings className="mr-2 h-5 w-5 animate-pulse" />
        설정 로딩 중...
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
      {/* Tab sidebar (desktop) */}
      <div className="hidden md:flex w-[200px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">설정</h2>
        </div>
        <nav className="flex-1 p-2" aria-label="설정 탭">
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
      <div className="flex overflow-x-auto border-b md:hidden" role="tablist" aria-label="설정 탭">
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
        {activeTab === "clinic" && <ClinicTab />}
        {activeTab === "messenger" && <MessengerTab />}
        {activeTab === "persona" && <PersonaTab />}
        {activeTab === "payment-settings" && <PaymentSettingsTab />}
        {activeTab === "settlements" && <SettlementsTab />}
      </div>
    </div>
  );
}
