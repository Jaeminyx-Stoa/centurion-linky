"use client";

import { useEffect, useState } from "react";
import {
  BookOpen,
  Languages,
  Plus,
  Trash2,
  Pencil,
  Search,
  AlertCircle,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useKnowledgeStore } from "@/stores/knowledge";
import type {
  ResponseLibrary,
  ResponseLibraryCreate,
  MedicalTerm,
  MedicalTermCreate,
} from "@/types/knowledge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type TabId = "response-library" | "medical-terms";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "response-library", label: "답변 라이브러리", icon: BookOpen },
  { id: "medical-terms", label: "의료 용어", icon: Languages },
];

const FAQ_CATEGORIES = [
  { value: "pricing", label: "가격" },
  { value: "procedure", label: "시술" },
  { value: "booking", label: "예약" },
  { value: "aftercare", label: "사후관리" },
  { value: "general", label: "일반" },
];

const TERM_CATEGORIES = [
  { value: "procedure", label: "시술" },
  { value: "symptom", label: "증상" },
  { value: "body_part", label: "부위" },
  { value: "material", label: "재료" },
  { value: "general", label: "일반" },
];

const LANGUAGES = [
  { code: "ko", label: "한국어" },
  { code: "en", label: "영어" },
  { code: "ja", label: "일본어" },
  { code: "zh-CN", label: "중국어(간)" },
  { code: "vi", label: "베트남어" },
];

function ResponseLibraryTab() {
  const {
    responseLibrary,
    fetchResponseLibrary,
    createResponseLibrary,
    updateResponseLibrary,
    deleteResponseLibrary,
  } = useKnowledgeStore();
  const { accessToken } = useAuthStore();

  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Create form
  const [newCategory, setNewCategory] = useState("general");
  const [newQuestion, setNewQuestion] = useState("");
  const [newAnswer, setNewAnswer] = useState("");
  const [newLanguage, setNewLanguage] = useState("ko");
  const [newTags, setNewTags] = useState("");

  // Edit form
  const [editQuestion, setEditQuestion] = useState("");
  const [editAnswer, setEditAnswer] = useState("");
  const [editCategory, setEditCategory] = useState("");

  const handleFilter = () => {
    if (accessToken) {
      fetchResponseLibrary(
        accessToken,
        filterCategory || undefined,
        searchQuery || undefined,
      ).catch(() => {});
    }
  };

  useEffect(() => {
    handleFilter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCategory]);

  const handleCreate = async () => {
    if (!accessToken || !newQuestion.trim() || !newAnswer.trim()) return;
    const data: ResponseLibraryCreate = {
      category: newCategory,
      question: newQuestion.trim(),
      answer: newAnswer.trim(),
      language_code: newLanguage,
      tags: newTags.trim()
        ? newTags.split(",").map((t) => t.trim())
        : undefined,
    };
    try {
      await createResponseLibrary(accessToken, data);
      setNewQuestion("");
      setNewAnswer("");
      setNewTags("");
      setShowCreate(false);
    } catch {
      // errors propagate to UI via store error state
    }
  };

  const startEdit = (entry: ResponseLibrary) => {
    setEditingId(entry.id);
    setEditQuestion(entry.question);
    setEditAnswer(entry.answer);
    setEditCategory(entry.category);
  };

  const handleUpdate = async () => {
    if (!accessToken || !editingId) return;
    try {
      await updateResponseLibrary(accessToken, editingId, {
        question: editQuestion,
        answer: editAnswer,
        category: editCategory,
      });
      setEditingId(null);
    } catch {
      // errors propagate to UI via store error state
    }
  };

  const handleDelete = async (id: string) => {
    if (!accessToken) return;
    if (!confirm("정말 삭제하시겠습니까?")) return;
    await deleteResponseLibrary(accessToken, id).catch(() => {});
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">답변 라이브러리</CardTitle>
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
          <div className="flex items-center gap-2 pt-2">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="rounded border px-2 py-1.5 text-xs"
            >
              <option value="">전체 카테고리</option>
              {FAQ_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
            <div className="flex flex-1 items-center gap-1">
              <Input
                placeholder="검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleFilter()}
                className="h-8 text-xs"
              />
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={handleFilter}
                aria-label="검색"
              >
                <Search className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {showCreate && (
            <div className="mb-4 space-y-3 rounded-lg border p-3">
              <div className="space-y-2">
                <Label>카테고리</Label>
                <div className="flex flex-wrap gap-2">
                  {FAQ_CATEGORIES.map((c) => (
                    <button
                      key={c.value}
                      onClick={() => setNewCategory(c.value)}
                      className={`rounded-md border px-3 py-1.5 text-xs transition-colors ${
                        newCategory === c.value
                          ? "border-primary bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="faq-question">질문</Label>
                <textarea
                  id="faq-question"
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  placeholder="고객이 자주 묻는 질문"
                  className="w-full rounded border px-3 py-2 text-sm"
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="faq-answer">답변</Label>
                <textarea
                  id="faq-answer"
                  value={newAnswer}
                  onChange={(e) => setNewAnswer(e.target.value)}
                  placeholder="AI가 참조할 답변 내용"
                  className="w-full rounded border px-3 py-2 text-sm"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>언어</Label>
                  <select
                    value={newLanguage}
                    onChange={(e) => setNewLanguage(e.target.value)}
                    className="w-full rounded border px-2 py-1.5 text-sm"
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="faq-tags">태그 (쉼표 구분)</Label>
                  <Input
                    id="faq-tags"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                    placeholder="보톡스, 가격"
                    className="h-8"
                  />
                </div>
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

          {responseLibrary.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              등록된 답변이 없습니다
            </p>
          ) : (
            <div className="space-y-3">
              {responseLibrary.map((entry) =>
                editingId === entry.id ? (
                  <div
                    key={entry.id}
                    className="space-y-3 rounded-lg border border-primary/30 p-3"
                  >
                    <div className="space-y-2">
                      <Label>카테고리</Label>
                      <select
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                        className="rounded border px-2 py-1.5 text-xs"
                      >
                        {FAQ_CATEGORIES.map((c) => (
                          <option key={c.value} value={c.value}>
                            {c.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>질문</Label>
                      <textarea
                        value={editQuestion}
                        onChange={(e) => setEditQuestion(e.target.value)}
                        className="w-full rounded border px-3 py-2 text-sm"
                        rows={2}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>답변</Label>
                      <textarea
                        value={editAnswer}
                        onChange={(e) => setEditAnswer(e.target.value)}
                        className="w-full rounded border px-3 py-2 text-sm"
                        rows={3}
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
                    key={entry.id}
                    className="flex items-start justify-between rounded-lg border p-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="rounded bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                          {FAQ_CATEGORIES.find(
                            (c) => c.value === entry.category,
                          )?.label || entry.category}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {LANGUAGES.find(
                            (l) => l.code === entry.language_code,
                          )?.label || entry.language_code}
                        </span>
                        {!entry.is_active && (
                          <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
                            비활성
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium">{entry.question}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                        {entry.answer}
                      </p>
                      {entry.tags && entry.tags.length > 0 && (
                        <div className="mt-1 flex gap-1">
                          {entry.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded bg-muted px-1.5 py-0.5 text-[10px]"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="ml-2 flex items-center gap-1">
                      <button
                        onClick={() => startEdit(entry)}
                        className="rounded p-1 text-muted-foreground hover:bg-muted"
                        aria-label="답변 수정"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                        aria-label="답변 삭제"
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

function MedicalTermsTab() {
  const {
    medicalTerms,
    fetchMedicalTerms,
    createMedicalTerm,
    updateMedicalTerm,
    deleteMedicalTerm,
  } = useKnowledgeStore();
  const { accessToken } = useAuthStore();

  const [showCreate, setShowCreate] = useState(false);
  const [filterCategory, setFilterCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Create form
  const [newTermKo, setNewTermKo] = useState("");
  const [newCategory, setNewCategory] = useState("procedure");
  const [newDescription, setNewDescription] = useState("");
  const [newTranslations, setNewTranslations] = useState<
    Record<string, string>
  >({});

  const handleFilter = () => {
    if (accessToken) {
      fetchMedicalTerms(
        accessToken,
        filterCategory || undefined,
        searchQuery || undefined,
      ).catch(() => {});
    }
  };

  useEffect(() => {
    handleFilter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCategory]);

  const handleCreate = async () => {
    if (!accessToken || !newTermKo.trim()) return;
    const data: MedicalTermCreate = {
      term_ko: newTermKo.trim(),
      category: newCategory,
      description: newDescription.trim() || undefined,
      translations: newTranslations,
    };
    try {
      await createMedicalTerm(accessToken, data);
      setNewTermKo("");
      setNewDescription("");
      setNewTranslations({});
      setShowCreate(false);
    } catch {
      // errors propagate to UI via store error state
    }
  };

  const handleDelete = async (id: string) => {
    if (!accessToken) return;
    if (!confirm("정말 삭제하시겠습니까?")) return;
    await deleteMedicalTerm(accessToken, id).catch(() => {});
  };

  const translationLangs = [
    { code: "en", label: "영어" },
    { code: "ja", label: "일본어" },
    { code: "zh-CN", label: "중국어(간)" },
    { code: "zh-TW", label: "중국어(번)" },
    { code: "vi", label: "베트남어" },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">의료 용어</CardTitle>
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
          <div className="flex items-center gap-2 pt-2">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="rounded border px-2 py-1.5 text-xs"
            >
              <option value="">전체 카테고리</option>
              {TERM_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
            <div className="flex flex-1 items-center gap-1">
              <Input
                placeholder="검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleFilter()}
                className="h-8 text-xs"
              />
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={handleFilter}
                aria-label="검색"
              >
                <Search className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {showCreate && (
            <div className="mb-4 space-y-3 rounded-lg border p-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="term-ko">한국어 용어</Label>
                  <Input
                    id="term-ko"
                    value={newTermKo}
                    onChange={(e) => setNewTermKo(e.target.value)}
                    placeholder="예: 보톡스"
                  />
                </div>
                <div className="space-y-2">
                  <Label>카테고리</Label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full rounded border px-2 py-1.5 text-sm"
                  >
                    {TERM_CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="term-desc">설명</Label>
                <Input
                  id="term-desc"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="용어에 대한 설명"
                />
              </div>
              <div className="space-y-2">
                <Label>번역</Label>
                <div className="grid grid-cols-2 gap-2">
                  {translationLangs.map((lang) => (
                    <div key={lang.code} className="flex items-center gap-2">
                      <span className="w-16 text-xs text-muted-foreground">
                        {lang.label}
                      </span>
                      <Input
                        value={newTranslations[lang.code] || ""}
                        onChange={(e) =>
                          setNewTranslations((prev) => ({
                            ...prev,
                            [lang.code]: e.target.value,
                          }))
                        }
                        className="h-7 text-xs"
                        placeholder={lang.label}
                      />
                    </div>
                  ))}
                </div>
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

          {medicalTerms.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              등록된 의료 용어가 없습니다
            </p>
          ) : (
            <div className="space-y-3">
              {medicalTerms.map((term) => (
                <div
                  key={term.id}
                  className="flex items-start justify-between rounded-lg border p-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {term.term_ko}
                      </span>
                      <span className="rounded bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                        {TERM_CATEGORIES.find(
                          (c) => c.value === term.category,
                        )?.label || term.category}
                      </span>
                      {term.is_verified && (
                        <span className="rounded bg-green-50 px-1.5 py-0.5 text-[10px] text-green-600">
                          인증
                        </span>
                      )}
                      {!term.is_active && (
                        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
                          비활성
                        </span>
                      )}
                    </div>
                    {term.description && (
                      <p className="text-xs text-muted-foreground">
                        {term.description}
                      </p>
                    )}
                    {Object.keys(term.translations).length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {Object.entries(term.translations).map(
                          ([lang, text]) => (
                            <span
                              key={lang}
                              className="rounded bg-muted px-1.5 py-0.5 text-[10px]"
                            >
                              {lang}: {text}
                            </span>
                          ),
                        )}
                      </div>
                    )}
                  </div>
                  <div className="ml-2 flex items-center gap-1">
                    <button
                      onClick={() => handleDelete(term.id)}
                      className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      aria-label="용어 삭제"
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
    </div>
  );
}

export default function KnowledgePage() {
  const { accessToken } = useAuthStore();
  const { isLoading, error, fetchAll } = useKnowledgeStore();
  const [activeTab, setActiveTab] = useState<TabId>("response-library");

  useEffect(() => {
    if (accessToken) {
      fetchAll(accessToken);
    }
  }, [accessToken, fetchAll]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <BookOpen className="mr-2 h-5 w-5 animate-pulse" />
        지식 데이터 로딩 중...
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
      {/* Tab sidebar (desktop) */}
      <div className="hidden md:flex w-[200px] flex-col border-r">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">지식 관리</h2>
        </div>
        <nav className="flex-1 p-2" aria-label="지식 관리 탭">
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
      <div className="flex overflow-x-auto border-b md:hidden" role="tablist" aria-label="지식 관리 탭">
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
        {activeTab === "response-library" && <ResponseLibraryTab />}
        {activeTab === "medical-terms" && <MedicalTermsTab />}
      </div>
    </div>
  );
}
