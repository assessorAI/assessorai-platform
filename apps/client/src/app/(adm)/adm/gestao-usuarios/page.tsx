import { AppHeader } from "@/components/app-header/app-header";
import { GestaoUsuarios } from "@/features/adm/gestao-usuarios/gestao-usuarios";
import { admService } from "@/api/adm/adm.service";
import { AdmSummaryResponse } from "@/api/adm/adm.types";


// Revalidar o cache da página a cada 60 segundos
export const revalidate = 60;

export default async function GestaoUsuariosPage() {
  const breadcrumb = [
    { label: "Painel", link: "/adm/dashboard" },
    { label: "Gestão de usuários", link: "/adm/gestao-usuarios" },
  ];

  const admSummary = (await admService.summary()) as AdmSummaryResponse;

  return (
    <article>
      <AppHeader title="Gestão de usuários" breadcrumb={breadcrumb} />
      <GestaoUsuarios
        activeUsersCount={admSummary.users.active}
        inactiveUsersCount={admSummary.users.inactive}
        totalUsersCount={admSummary.users.total}
      />
    </article>
  );
}
