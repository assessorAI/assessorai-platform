import { SessionProvider } from "next-auth/react";

import { Toaster } from "sonner";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { RouteProgressProvider } from "./../../providers/route-progress-provider";
import { SessionMonitor } from "@/components/session-monitor";
import { AdmMenu } from "@/components/app-menu/adm-menu";
import { ReactQueryProvider } from "@/providers/react-query.provider";


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
          <AdmMenu />
          <SidebarTrigger />
          <main className="adm-layout-main">
          <RouteProgressProvider>
            <ReactQueryProvider>
              {children}
            </ReactQueryProvider>
            </RouteProgressProvider>
          </main>
        </SidebarProvider>
      </SessionProvider>
    </>
  );
}
