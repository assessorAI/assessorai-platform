import { AppHeader } from "@/components/app-header/app-header";
import { GestaoMandatos } from "@/features/adm/gestao-mandatos/gestao-mandatos";

export default async function GestaoMandatosPage() {
  const breadcrumb = [
    { label: "Painel", link: "/adm/dashboard" },
    { label: "Gestão de mandatos", link: "/adm/gestao-mandatos" },
  ];

  return (
    <article>
      <AppHeader title="Gestão de mandatos" breadcrumb={breadcrumb} />
      <GestaoMandatos />
    </article>
  );
}
