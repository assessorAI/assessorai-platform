"use client";

import { ProgressBarProvider } from "react-transition-progress";
import RouteProgress from "@/components/ui/route-progress";

export function RouteProgressProvider({ children }: { children: React.ReactNode }) {
  return (
    <ProgressBarProvider>
      {children}
      <RouteProgress />
    </ProgressBarProvider>
  );
}
