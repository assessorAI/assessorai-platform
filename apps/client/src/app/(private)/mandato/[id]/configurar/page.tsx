import { AppHeader } from "@/components/app-header/app-header";
import { ConfigurarMandato } from "@/features/configurar-mandato/configurar-mandato";
import { redirect } from "next/navigation";
import { auth } from "@/api/auth/index";
import { mandatoService } from "@/api/mandato/mandato.service";
import { DocumentosCasaResponse } from "@/types/documentos-casa.types";
import { PermissionLevel } from "@/types/user.types";
import { hasPermission } from "@/lib/check-permissions";

export default async function ConfigurarMandatoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const session = await auth();

  if (!session) {
    redirect("/login");
  }

  const mandato = await mandatoService.getMandato(id);
  const users = (await mandatoService.getMandatoUsers(mandato.id.toString())).users;
  const documents = await mandatoService.getMandatoDocuments(mandato.id.toString()) as DocumentosCasaResponse;

  const permissionLevel = session.user?.permission_level;

  const canEditMandato = hasPermission(permissionLevel as PermissionLevel, "mandato:edit");

  return (
    <article>
      <AppHeader
        title={canEditMandato ? "Configurar seu mandato" : "Dados do mandato"}
        breadcrumb={[
          { label: "Painel", link: "/dashboard" },
          {
            label: canEditMandato ? "Configurar seu mandato" : "Dados do mandato",
            link: `/mandato/${id}/configurar`,
          },
        ]}
      />
      <ConfigurarMandato 
        mandato={mandato} 
        users={users} 
        documents={documents.files} 
      />
    </article>
  );
}
