import { AppHeader } from "@/components/app-header/app-header";

export default function DashboardPage() {
  return (
    <article className="flex flex-col h-screen">
      <AppHeader title="Administrador" />
      <iframe
        className="flex-1 w-full"
        src="https://lookerstudio.google.com/embed/reporting/f543e7cc-eb45-4fe9-b8ff-f37f61a66ebf/page/p_hqtdyc86wd&rm=minimal&embedded=true"
        style={{ border: "0" }}
        allowFullScreen
        sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
      />
    </article>
  );
}
