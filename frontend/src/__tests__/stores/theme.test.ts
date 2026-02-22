import { beforeEach, describe, expect, it } from "vitest";

import { useUIStore } from "@/stores/ui";

describe("useUIStore - theme", () => {
  beforeEach(() => {
    useUIStore.setState({
      sidebarExpanded: false,
      mobileMenuOpen: false,
      theme: "system",
    });
  });

  it("defaults to system theme", () => {
    const state = useUIStore.getState();
    expect(state.theme).toBe("system");
  });

  it("setTheme updates to dark", () => {
    useUIStore.getState().setTheme("dark");
    expect(useUIStore.getState().theme).toBe("dark");
  });

  it("setTheme updates to light", () => {
    useUIStore.getState().setTheme("light");
    expect(useUIStore.getState().theme).toBe("light");
  });

  it("cycles through themes", () => {
    const { setTheme } = useUIStore.getState();

    setTheme("light");
    expect(useUIStore.getState().theme).toBe("light");

    setTheme("dark");
    expect(useUIStore.getState().theme).toBe("dark");

    setTheme("system");
    expect(useUIStore.getState().theme).toBe("system");
  });
});
