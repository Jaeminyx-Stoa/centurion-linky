import { describe, expect, it } from "vitest";

import ko from "@/i18n/ko";
import en from "@/i18n/en";
import ja from "@/i18n/ja";
import zh from "@/i18n/zh";
import vi from "@/i18n/vi";

const koKeys = Object.keys(ko).sort();

describe("i18n locale completeness", () => {
  it("en has the same keys as ko", () => {
    expect(Object.keys(en).sort()).toEqual(koKeys);
  });

  it("ja has the same keys as ko", () => {
    expect(Object.keys(ja).sort()).toEqual(koKeys);
  });

  it("zh has the same keys as ko", () => {
    expect(Object.keys(zh).sort()).toEqual(koKeys);
  });

  it("vi has the same keys as ko", () => {
    expect(Object.keys(vi).sort()).toEqual(koKeys);
  });

  it("no empty values in ja", () => {
    for (const [key, value] of Object.entries(ja)) {
      expect(value, `ja key "${key}" should not be empty`).not.toBe("");
    }
  });

  it("no empty values in zh", () => {
    for (const [key, value] of Object.entries(zh)) {
      expect(value, `zh key "${key}" should not be empty`).not.toBe("");
    }
  });

  it("no empty values in vi", () => {
    for (const [key, value] of Object.entries(vi)) {
      expect(value, `vi key "${key}" should not be empty`).not.toBe("");
    }
  });
});
