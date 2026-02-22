"use client";

import { useEffect, useState } from "react";
import { Camera, CheckCircle, Image, Trash2 } from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { useTreatmentPhotoStore } from "@/stores/treatment-photo";
import { useT } from "@/i18n";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type TabId = "gallery" | "pairs" | "portfolio";

const TABS: { id: TabId; label: string }[] = [
  { id: "gallery", label: "전체 사진" },
  { id: "pairs", label: "Before/After" },
  { id: "portfolio", label: "포트폴리오" },
];

export default function TreatmentPhotosPage() {
  const { accessToken } = useAuthStore();
  const t = useT();
  const {
    photos,
    pairs,
    total,
    isLoading,
    fetchPhotos,
    fetchPairs,
    approvePhoto,
    deletePhoto,
  } = useTreatmentPhotoStore();
  const [activeTab, setActiveTab] = useState<TabId>("gallery");

  useEffect(() => {
    if (!accessToken) return;
    if (activeTab === "gallery") {
      fetchPhotos(accessToken);
    } else if (activeTab === "pairs") {
      fetchPairs(accessToken);
    } else if (activeTab === "portfolio") {
      fetchPhotos(accessToken, { portfolio_only: true });
    }
  }, [accessToken, activeTab, fetchPhotos, fetchPairs]);

  const handleApprove = async (photoId: string) => {
    if (!accessToken) return;
    await approvePhoto(accessToken, photoId);
    fetchPhotos(accessToken);
  };

  const handleDelete = async (photoId: string) => {
    if (!accessToken) return;
    await deletePhoto(accessToken, photoId);
    fetchPhotos(accessToken);
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="border-b px-6 py-3">
        <h1 className="text-lg font-semibold">{t("photos.title")}</h1>
      </div>

      {/* Tabs */}
      <div className="flex border-b px-6" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`px-4 py-2 text-sm ${
              activeTab === tab.id
                ? "border-b-2 border-primary text-primary font-medium"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        ) : activeTab === "pairs" ? (
          /* Before/After Pairs View */
          pairs.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("photos.empty")}</p>
          ) : (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {pairs.map((pair) => (
                <Card key={pair.pair_id}>
                  <CardContent className="pt-4">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <p className="mb-1 text-center text-xs font-medium text-muted-foreground">
                          Before
                        </p>
                        {pair.before ? (
                          <div className="aspect-square rounded bg-muted flex items-center justify-center overflow-hidden">
                            <Image className="h-8 w-8 text-muted-foreground" />
                          </div>
                        ) : (
                          <div className="aspect-square rounded border-2 border-dashed flex items-center justify-center">
                            <Camera className="h-6 w-6 text-muted-foreground" />
                          </div>
                        )}
                      </div>
                      <div>
                        <p className="mb-1 text-center text-xs font-medium text-muted-foreground">
                          After
                        </p>
                        {pair.after ? (
                          <div className="aspect-square rounded bg-muted flex items-center justify-center overflow-hidden">
                            <Image className="h-8 w-8 text-muted-foreground" />
                          </div>
                        ) : (
                          <div className="aspect-square rounded border-2 border-dashed flex items-center justify-center">
                            <Camera className="h-6 w-6 text-muted-foreground" />
                          </div>
                        )}
                      </div>
                    </div>
                    {pair.after?.days_after_procedure && (
                      <p className="mt-2 text-center text-xs text-muted-foreground">
                        {pair.after.days_after_procedure}{t("photos.daysAfter")}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )
        ) : (
          /* Gallery / Portfolio View */
          photos.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("photos.empty")}</p>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {t("common.total")}: {total}
              </p>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {photos.map((photo) => (
                  <Card key={photo.id} className="overflow-hidden">
                    <div className="aspect-square bg-muted flex items-center justify-center">
                      <Image className="h-10 w-10 text-muted-foreground" />
                    </div>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between">
                        <span
                          className={`rounded px-2 py-0.5 text-xs ${
                            photo.photo_type === "before"
                              ? "bg-blue-100 text-blue-700"
                              : photo.photo_type === "after"
                                ? "bg-green-100 text-green-700"
                                : "bg-purple-100 text-purple-700"
                          }`}
                        >
                          {photo.photo_type}
                        </span>
                        <div className="flex items-center gap-1">
                          {photo.is_consent_given && (
                            <span className="text-xs text-green-600" title={t("photos.consentGiven")}>
                              {t("photos.consent")}
                            </span>
                          )}
                        </div>
                      </div>
                      {photo.description && (
                        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                          {photo.description}
                        </p>
                      )}
                      <div className="mt-2 flex gap-1">
                        {!photo.is_portfolio_approved && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs"
                            onClick={() => handleApprove(photo.id)}
                          >
                            <CheckCircle className="mr-1 h-3 w-3" />
                            {t("photos.approve")}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs text-destructive"
                          onClick={() => handleDelete(photo.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
