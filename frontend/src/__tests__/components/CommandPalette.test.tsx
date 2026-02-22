import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { CommandPalette } from "@/components/dashboard/command-palette";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("CommandPalette", () => {
  it("is not visible by default", () => {
    render(<CommandPalette />);
    expect(screen.queryByTestId("command-palette")).not.toBeInTheDocument();
  });

  it("opens when Ctrl+K is pressed", () => {
    render(<CommandPalette />);
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.getByTestId("command-palette")).toBeInTheDocument();
  });

  it("shows navigation items when open", () => {
    render(<CommandPalette />);
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.getByText("대시보드")).toBeInTheDocument();
    expect(screen.getByText("받은 메시지")).toBeInTheDocument();
    expect(screen.getByText("설정")).toBeInTheDocument();
  });

  it("closes when Ctrl+K is pressed again", () => {
    render(<CommandPalette />);
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.getByTestId("command-palette")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.queryByTestId("command-palette")).not.toBeInTheDocument();
  });
});
