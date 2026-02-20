"use client";

import React from "react";
import { AlertCircle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
          <AlertCircle className="h-10 w-10 text-destructive" />
          <div className="text-center">
            <h2 className="text-lg font-semibold">오류가 발생했습니다</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              페이지를 새로고침하거나 다시 시도해 주세요
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => this.setState({ hasError: false })}
          >
            <RefreshCcw className="mr-2 h-4 w-4" />
            다시 시도
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
