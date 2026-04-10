import { SessionProvider } from "next-auth/react";

import { Toaster } from "sonner";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { RouteProgressProvider } from "./../../providers/route-progress-provider";
import { SessionMonitor } from "@/components/session-monitor";
import { PrivateMenu } from "@/components/app-menu/private-menu";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Toaster richColors position="top-center" />
      <SessionProvider>
        <SessionMonitor />
        <SidebarProvider>
          <PrivateMenu />
          <SidebarTrigger />
          <main className="layout-main">
          <RouteProgressProvider>
            {children}
            </RouteProgressProvider>
          </main>
        </SidebarProvider>
      </SessionProvider>
    </>
  );
}
