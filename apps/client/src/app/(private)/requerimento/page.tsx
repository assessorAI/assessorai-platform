import { AppHeader } from "@/components/app-header/app-header";
import { Metadata } from "next";
import { Requerimento } from "@/features/requerimento/requerimento";

export const metadata: Metadata = {
    title: "Requerimentos e indicações - Assesorai"
  }

const appHeader = {
  title: "Requerimentos e indicações",
  breadcrumb: [
    { label: "Painel", link: "/dashboard" },
    { label: "Requerimentos e indicações", link: "/requerimento" },
  ]
}
export default function RequerimentoPage() {
  return (
    <article>
      <AppHeader {...appHeader} />
      <Requerimento />
    </article>
  );
}