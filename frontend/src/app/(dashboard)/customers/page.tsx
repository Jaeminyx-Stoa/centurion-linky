"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Search,
  AlertCircle,
  X,
  Globe,
  Tag,
  Save,
  Plus,
  Trash2,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useCustomerStore } from "@/stores/customer";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ListSkeleton } from "@/components/shared/skeletons";
import { PaginationControls } from "@/components/shared/pagination-controls";
import type { Customer, HealthData, HealthItem } from "@/types/customer";
import { useT } from "@/i18n";

const MESSENGER_FILTERS = [
  { id: "all", label: "전체" },
  { id: "telegram", label: "Telegram" },
  { id: "instagram", label: "Instagram" },
  { id: "facebook", label: "Facebook" },
  { id: "whatsapp", label: "WhatsApp" },
  { id: "line", label: "LINE" },
  { id: "kakao", label: "KakaoTalk" },
];

function HealthItemList({
  label,
  items,
  onChange,
  addLabel,
}: {
  label: string;
  items: HealthItem[];
  onChange: (items: HealthItem[]) => void;
  addLabel: string;
}) {
  const [newName, setNewName] = useState("");

  const handleAdd = () => {
    if (!newName.trim()) return;
    onChange([...items, { name: newName.trim() }]);
    setNewName("");
  };

  const handleRemove = (idx: number) => {
    onChange(items.filter((_, i) => i !== idx));
  };

  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      {items.map((item, idx) => (
        <div key={idx} className="flex items-center gap-1">
          <span className="flex-1 rounded border px-2 py-1 text-xs">
            {item.name}
          </span>
          <button
            onClick={() => handleRemove(idx)}
            className="rounded p-0.5 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      ))}
      <div className="flex gap-1">
        <Input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          className="h-7 text-xs"
          placeholder={addLabel}
        />
        <Button variant="outline" size="sm" className="h-7 px-2" onClick={handleAdd}>
          <Plus className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

function CustomerDetail({
  customer,
  onClose,
}: {
  customer: Customer;
  onClose: () => void;
}) {
  const { accessToken } = useAuthStore();
  const { updateCustomer } = useCustomerStore();
  const t = useT();
  const [name, setName] = useState(customer.name || "");
  const [phone, setPhone] = useState(customer.phone || "");
  const [email, setEmail] = useState(customer.email || "");
  const [notes, setNotes] = useState(customer.notes || "");
  const [conditions, setConditions] = useState<HealthItem[]>(
    customer.medical_conditions?.items || [],
  );
  const [allergies, setAllergies] = useState<HealthItem[]>(
    customer.allergies?.items || [],
  );
  const [medications, setMedications] = useState<HealthItem[]>(
    customer.medications?.items || [],
  );

  const handleSave = async () => {
    if (!accessToken) return;
    await updateCustomer(accessToken, customer.id, {
      name: name || undefined,
      phone: phone || undefined,
      email: email || undefined,
      notes: notes || undefined,
      medical_conditions: { items: conditions },
      allergies: { items: allergies },
      medications: { items: medications },
    });
  };

  return (
    <div className="fixed inset-0 z-20 bg-background md:relative md:inset-auto md:z-auto md:w-[360px] flex flex-col border-l">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold">고객 상세</h3>
        <button
          onClick={onClose}
          className="rounded p-1 hover:bg-muted"
          aria-label="패널 닫기"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-lg font-bold text-primary">
            {(customer.display_name || customer.name || "?")[0]}
          </div>
          <p className="font-medium">
            {customer.display_name || customer.name || "이름 없음"}
          </p>
          <p className="text-xs text-muted-foreground">
            {customer.messenger_type}
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <Globe className="h-4 w-4 text-muted-foreground" />
            <span>{customer.country_code || "-"}</span>
            <span className="text-muted-foreground">
              {customer.language_code || ""}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Tag className="h-4 w-4 text-muted-foreground" />
            <span>예약 {customer.total_bookings}건</span>
          </div>
          {customer.tags && customer.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {customer.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded bg-muted px-2 py-0.5 text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Health Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("customers.healthInfo")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <HealthItemList
              label={t("customers.medicalConditions")}
              items={conditions}
              onChange={setConditions}
              addLabel={t("customers.addItem")}
            />
            <HealthItemList
              label={t("customers.allergies")}
              items={allergies}
              onChange={setAllergies}
              addLabel={t("customers.addItem")}
            />
            <HealthItemList
              label={t("customers.medications")}
              items={medications}
              onChange={setMedications}
              addLabel={t("customers.addItem")}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">정보 수정</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1">
              <Label htmlFor="cust-name" className="text-xs">
                이름
              </Label>
              <Input
                id="cust-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="cust-phone" className="text-xs">
                전화번호
              </Label>
              <Input
                id="cust-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="cust-email" className="text-xs">
                이메일
              </Label>
              <Input
                id="cust-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="cust-notes" className="text-xs">
                메모
              </Label>
              <textarea
                id="cust-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm"
                rows={3}
              />
            </div>
            <Button size="sm" onClick={handleSave}>
              <Save className="mr-1 h-3 w-3" />
              저장
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function CustomersPage() {
  const { accessToken } = useAuthStore();
  const {
    customers, isLoading, error, total, page, pageSize,
    fetchCustomers, setPage,
  } = useCustomerStore();
  const [search, setSearch] = useState("");
  const [messengerFilter, setMessengerFilter] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (accessToken) {
      fetchCustomers(accessToken);
    }
  }, [accessToken, fetchCustomers, page]);

  const filtered = customers.filter((c) => {
    const matchesSearch =
      !search ||
      (c.name || "").toLowerCase().includes(search.toLowerCase()) ||
      (c.display_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (c.email || "").toLowerCase().includes(search.toLowerCase()) ||
      (c.phone || "").includes(search);
    const matchesMessenger =
      messengerFilter === "all" || c.messenger_type === messengerFilter;
    return matchesSearch && matchesMessenger;
  });

  const selectedCustomer = selectedId
    ? customers.find((c) => c.id === selectedId) || null
    : null;

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b px-6 py-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              <h1 className="text-lg font-bold">고객 관리</h1>
            </div>
            <span className="text-sm text-muted-foreground">
              {total}명
            </span>
          </div>
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="이름, 이메일, 전화번호 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          {/* Messenger Filter */}
          <div className="flex gap-2 overflow-x-auto">
            {MESSENGER_FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => setMessengerFilter(f.id)}
                aria-pressed={messengerFilter === f.id}
                className={`whitespace-nowrap rounded-full px-3 py-1 text-xs transition-colors ${
                  messengerFilter === f.id
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

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <ListSkeleton />
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
              <Users className="mb-2 h-8 w-8" />
              <p className="text-sm">고객이 없습니다</p>
            </div>
          ) : (
            <div className="divide-y">
              {filtered.map((customer) => (
                <button
                  key={customer.id}
                  onClick={() =>
                    setSelectedId(
                      selectedId === customer.id ? null : customer.id,
                    )
                  }
                  className={`flex w-full items-center justify-between px-6 py-3 text-left hover:bg-muted/50 ${
                    selectedId === customer.id ? "bg-muted/50" : ""
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                      {(
                        customer.display_name ||
                        customer.name ||
                        "?"
                      )[0]}
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        {customer.display_name ||
                          customer.name ||
                          "이름 없음"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {customer.messenger_type}
                        {customer.country_code &&
                          ` | ${customer.country_code}`}
                        {customer.email && ` | ${customer.email}`}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      예약 {customer.total_bookings}건
                    </p>
                    <p className="text-[10px] text-muted-foreground/60">
                      {new Date(customer.created_at).toLocaleDateString(
                        "ko-KR",
                      )}
                    </p>
                  </div>
                </button>
              ))}
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

      {/* Detail Panel */}
      {selectedCustomer && (
        <CustomerDetail
          customer={selectedCustomer}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
