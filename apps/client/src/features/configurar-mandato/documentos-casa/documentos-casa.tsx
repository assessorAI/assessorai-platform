import { Card, CardContent, CardHeader } from "@/components/ui/card";
import styles from "./documentos-casa.module.scss";

import {
  DocumentosCasa as DocumentosCasaType } from "@/types/documentos-casa.types";
import { useSession } from "next-auth/react";
import { hasPermission } from "@/lib/check-permissions";
import { PermissionLevel } from "@/types/user.types";
import { DocumentosCasaForm } from "./documentos-casa-form";
import { DocumentosCasaTable } from "./documentos-casa-table";

export function DocumentosCasa({
  mandatoId,
  documents,
}: {
  mandatoId: string;
  documents: DocumentosCasaType[];
}) {
  const { data: session } = useSession();
  const permissionLevel = session?.user?.permission_level;

  const canEditDocuments = hasPermission(permissionLevel as PermissionLevel, "mandato:documents:edit");

  return (
    <Card className={styles.container}>
      <CardHeader className={styles.header}>
        <h2 className={styles.title}>Documentos da casa</h2>
      </CardHeader>

      <CardContent className={styles.content}>

    {canEditDocuments ? <DocumentosCasaForm mandatoId={mandatoId} /> : null}
        <DocumentosCasaTable documents={documents} />
      </CardContent>
    </Card>
  );
}
