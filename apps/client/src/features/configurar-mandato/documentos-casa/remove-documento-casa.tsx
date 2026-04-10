import {
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { TrashIcon } from "@heroicons/react/24/outline";

import styles from "./documentos-casa.module.scss";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogCancel,
  AlertDialogAction,
  AlertDialogFooter,
  AlertDialogContent,
} from "@/components/ui/alert-dialog";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";

export function RemoveDocumentoCasa({ id, title }: { id: string, title: string }) {
  const router = useRouter();

  const handleRemove = async (id: string) => {
    try {
      await restClient(`/api/documentos-casa?file_id=${id}`, {
        method: "DELETE",
      });

      toast.success("Documento removido com sucesso");
      router.refresh();
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger>
        <DropdownMenuItem
          className={styles.actionsRemoveDocument}
          onSelect={(e) => e.preventDefault()}
        >
          <TrashIcon className="h-4 w-4" />
          Remover arquivo
        </DropdownMenuItem>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remover arquivo</AlertDialogTitle>
          <AlertDialogDescription>
            Tem certeza que deseja remover o arquivo <strong>{title}</strong>?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction 
          className={styles.buttonRemoveDocument}
          onClick={() => handleRemove(id)}>
            Remover
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
