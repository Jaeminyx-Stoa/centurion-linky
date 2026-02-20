import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { PaginationControls } from "@/components/shared/pagination-controls";

// Mock i18n to avoid zustand/persist issues in tests
vi.mock("@/i18n", () => ({
  useT: () => (key: string, params?: Record<string, string | number>) => {
    const translations: Record<string, string> = {
      "pagination.showing": `${params?.start}-${params?.end} of ${params?.total}`,
      "pagination.prev": "Previous",
      "pagination.next": "Next",
    };
    return translations[key] ?? key;
  },
}));

describe("PaginationControls", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders nothing when total fits in one page", () => {
    const { container } = render(
      <PaginationControls page={1} pageSize={20} total={15} onPageChange={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders pagination when multiple pages exist", () => {
    render(
      <PaginationControls page={1} pageSize={20} total={50} onPageChange={vi.fn()} />,
    );
    expect(screen.getByText("1-20 of 50")).toBeInTheDocument();
    expect(screen.getByText("1 / 3")).toBeInTheDocument();
  });

  it("disables previous button on first page", () => {
    render(
      <PaginationControls page={1} pageSize={20} total={50} onPageChange={vi.fn()} />,
    );
    const prevButton = screen.getByLabelText("Previous");
    expect(prevButton).toBeDisabled();
  });

  it("disables next button on last page", () => {
    render(
      <PaginationControls page={3} pageSize={20} total={50} onPageChange={vi.fn()} />,
    );
    const nextButton = screen.getByLabelText("Next");
    expect(nextButton).toBeDisabled();
  });

  it("calls onPageChange with next page", () => {
    const onPageChange = vi.fn();
    render(
      <PaginationControls page={1} pageSize={20} total={50} onPageChange={onPageChange} />,
    );
    fireEvent.click(screen.getByLabelText("Next"));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageChange with previous page", () => {
    const onPageChange = vi.fn();
    render(
      <PaginationControls page={2} pageSize={20} total={50} onPageChange={onPageChange} />,
    );
    fireEvent.click(screen.getByLabelText("Previous"));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it("shows correct range for middle page", () => {
    render(
      <PaginationControls page={2} pageSize={20} total={50} onPageChange={vi.fn()} />,
    );
    expect(screen.getByText("21-40 of 50")).toBeInTheDocument();
  });

  it("shows correct range for last partial page", () => {
    render(
      <PaginationControls page={3} pageSize={20} total={50} onPageChange={vi.fn()} />,
    );
    expect(screen.getByText("41-50 of 50")).toBeInTheDocument();
  });
});
