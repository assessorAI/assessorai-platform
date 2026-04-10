import { Button } from "@/components/ui/button";

import { TableCell } from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { EllipsisHorizontalIcon, TrashIcon } from "@heroicons/react/24/outline";

import styles from "./minha-equipe-table.module.scss";
import { toast } from "sonner";
import { useParams, useRouter } from "next/navigation";
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

export function RemoveMember({ id, email }: { id: number, email: string }) {
  const { id: mandatoId } = useParams();
  const router = useRouter();

  const handleRemove = async (id: number) => {
    try {
      await restClient(`/api/mandato/${mandatoId}/users/${id}`, {
        method: "DELETE",
      });

      toast.success("Membro removido com sucesso");
      router.refresh();
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    }
  };

  const alertRemoveMember = (
    <AlertDialog>
      <AlertDialogTrigger>
        <DropdownMenuItem
          className={styles.actionsRemoveUser}
          onSelect={(e) => e.preventDefault()}
        >
          <TrashIcon className="h-4 w-4" />
          Remover usuário
        </DropdownMenuItem>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remover membro</AlertDialogTitle>
          <AlertDialogDescription>
            Tem certeza que deseja remover <strong>{email}</strong> do mandato?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction 
          className={styles.buttonRemoveMember}
          onClick={() => handleRemove(id)}>
            Remover
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );

  return (
    <TableCell className={styles.actionsCell}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost">
            <EllipsisHorizontalIcon className={styles.actionsIcon} />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {alertRemoveMember}
        </DropdownMenuContent>
      </DropdownMenu>
    </TableCell>
  );
}
