import { afterEach, describe, expect, it } from "vitest";

import { useI18nStore } from "@/i18n";
import ko from "@/i18n/ko";
import en from "@/i18n/en";

describe("i18n", () => {
  afterEach(() => {
    useI18nStore.setState({ locale: "ko" });
  });

  describe("translation dictionaries", () => {
    it("ko and en have the same keys", () => {
      const koKeys = Object.keys(ko).sort();
      const enKeys = Object.keys(en).sort();
      expect(koKeys).toEqual(enKeys);
    });

    it("no empty values in ko", () => {
      for (const [key, value] of Object.entries(ko)) {
        expect(value, `ko["${key}"] should not be empty`).toBeTruthy();
      }
    });

    it("no empty values in en", () => {
      for (const [key, value] of Object.entries(en)) {
        expect(value, `en["${key}"] should not be empty`).toBeTruthy();
      }
    });
  });

  describe("useI18nStore", () => {
    it("defaults to Korean locale", () => {
      expect(useI18nStore.getState().locale).toBe("ko");
    });

    it("can switch to English", () => {
      useI18nStore.getState().setLocale("en");
      expect(useI18nStore.getState().locale).toBe("en");
    });

    it("can switch back to Korean", () => {
      useI18nStore.getState().setLocale("en");
      useI18nStore.getState().setLocale("ko");
      expect(useI18nStore.getState().locale).toBe("ko");
    });
  });

  describe("translation content", () => {
    it("has all navigation keys", () => {
      const navKeys = Object.keys(ko).filter((k) => k.startsWith("nav."));
      expect(navKeys.length).toBeGreaterThanOrEqual(11);
    });

    it("has common action keys", () => {
      expect(ko["common.save"]).toBe("저장");
      expect(en["common.save"]).toBe("Save");
    });

    it("has pagination keys with interpolation placeholders", () => {
      expect(ko["pagination.showing"]).toContain("{start}");
      expect(ko["pagination.showing"]).toContain("{end}");
      expect(ko["pagination.showing"]).toContain("{total}");
      expect(en["pagination.showing"]).toContain("{start}");
    });
  });
});
