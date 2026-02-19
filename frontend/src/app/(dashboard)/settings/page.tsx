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
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useSettingsStore } from "@/stores/settings";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type TabId = "clinic" | "messenger" | "persona";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "clinic", label: "클리닉 정보", icon: Building2 },
  { id: "messenger", label: "메신저 계정", icon: MessageSquare },
  { id: "persona", label: "AI 페르소나", icon: Bot },
];

const PLATFORM_LABELS: Record<string, string> = {
  telegram: "Telegram",
  line: "LINE",
  instagram: "Instagram",
  facebook: "Facebook",
  whatsapp: "WhatsApp",
  kakao: "KakaoTalk",
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
  const { messengerAccounts } = useSettingsStore();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">연동된 메신저 계정</CardTitle>
        </CardHeader>
        <CardContent>
          {messengerAccounts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              연동된 메신저 계정이 없습니다
            </p>
          ) : (
            <div className="space-y-3">
              {messengerAccounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <MessageSquare className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">
                        {account.account_name ||
                          PLATFORM_LABELS[account.platform] ||
                          account.platform}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {PLATFORM_LABELS[account.platform] || account.platform}
                        {account.account_id && ` (${account.account_id})`}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      account.is_active
                        ? "bg-green-50 text-green-600"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {account.is_active ? "활성" : "비활성"}
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
    <div className="flex flex-1 overflow-hidden">
      {/* Tab sidebar */}
      <div className="flex w-[200px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">설정</h2>
        </div>
        <nav className="flex-1 p-2">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
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
      </div>
    </div>
  );
}
