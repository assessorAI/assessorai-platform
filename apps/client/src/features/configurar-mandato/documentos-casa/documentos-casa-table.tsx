import {
  Table,
  TableHead,
  TableBody,
  TableHeader,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { DocumentosCasa } from "@/types/documentos-casa.types";
import { RemoveDocumentoCasa } from "./remove-documento-casa";
import { DownloadDocumentoCasa } from "./download-documento-casa";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { EllipsisHorizontalIcon } from "@heroicons/react/24/outline";
import { useSession } from "next-auth/react";
import { PermissionLevel } from "@/types/user.types";
import { hasPermission } from "@/lib/check-permissions";

export function DocumentosCasaTable({
  documents,
}: {
  documents: DocumentosCasa[];
}) {
  const { data: session } = useSession();
  const permissionLevel = session?.user?.permission_level;

  const canDeleteDocuments = hasPermission(permissionLevel as PermissionLevel, "mandato:documents:delete");
  
  if (documents.length === 0) {
    return (
      <Table>
        <TableBody>
          <TableRow>
            <TableCell colSpan={3} className="text-center">Não há documentos cadastrados</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome do documento</TableHead>
          <TableHead>Tipo de documento</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((document, index) => (
          <TableRow key={index}>
            <TableCell>{document.filename}</TableCell>
            <TableCell>{document.file_type}</TableCell>
            <TableCell>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost">
                  <EllipsisHorizontalIcon className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DownloadDocumentoCasa
                  id={document.id}
                  filename={document.filename}
                />
                {canDeleteDocuments ? <RemoveDocumentoCasa id={document.id} title={document.filename} /> : null}
              </DropdownMenuContent>
            </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
