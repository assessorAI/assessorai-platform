"use client";

import { Mandato } from "@/api/mandato/mandato.types";
import { UserResponse } from "@/api/user/user.types";
import { Badge } from "@/components/ui/badge";
import { ColumnDef } from "@tanstack/react-table";
import { PermissionLevel } from "@/types/user.types";
import { Button } from "@/components/ui/button";
import { TrashIcon } from "@heroicons/react/24/outline";
import { AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { DeleteUserDialog } from "@/components/dialogs";
import { restClient } from "@/lib/rest-client";
import { toast } from "sonner";
import { AppThrowError } from "@/api/error/app-throw-error";
import { QueryClient, useQueryClient } from "@tanstack/react-query";
import { Suspense } from "react";
import { cn } from "@/lib/utils";
import { ShowMandato } from "../../gestao-mandatos/show-mandato/show-mandato";
import { Spinner } from "@/components/ui/spinner";
import { Sheet, SheetTrigger } from "@/components/ui/sheet";
import { SheetContent } from "@/components/ui/sheet";
import { getDateFromIso } from "@/lib/get-date-from-iso";
import { headerWithOrderBy } from "@/components/data-table/sort-button";

const getPermissionLabel = (level: PermissionLevel) => {
  switch (level) {
    case PermissionLevel.Admin:
      return "Administrador";
    case PermissionLevel.Manager:
      return "Gerente do mandato";
    case PermissionLevel.User:
      return "Membro do mandato";
    case PermissionLevel.Viewer:
      return "Visualizador";
    default:
      return "";
  }
};

const handleDelete = async (id: string, queryClient: QueryClient) => {
  try {
    await restClient(`/api/user/${id}`, {
      method: "DELETE",
    });

    // atualiza a lista de usuários
    await queryClient.invalidateQueries({ queryKey: ["users"] });

    toast.success("Usuário removido com sucesso");
  } catch (error) {
    const errorMessage = error as AppThrowError;
    toast.error(errorMessage.customMessage!);
  }
};

function DeleteActionCell({ user }: { user: UserResponse }) {
  const queryClient = useQueryClient();

  return (
    <div onClick={(e) => e.stopPropagation()}>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="ghost" size="icon" className="size-4 hover:bg-destructive/10">
            <TrashIcon className="text-destructive" />
          </Button>
        </AlertDialogTrigger>
        <DeleteUserDialog
          name={user.first_name}
          onConfirm={() => handleDelete(user.id, queryClient)}
          onCancel={() => { }} />
      </AlertDialog>
    </div>
  );
}

export const columns: ColumnDef<UserResponse>[] = [
  {
    accessorKey: "first_name",
    meta: {
      label: "Nome",
    },
    header: ({ column, table }) => {
      return headerWithOrderBy(column, table);
    },
    cell: ({ row }) => {
      return (
        row.original.first_name && row.original.last_name ? (
          <div>
            {row.getValue("first_name")} {row.original.last_name}
          </div>
        ) : (
          <div className="text-gray-400">Nome não definido</div>
        )
      );
    },
  },
  {
    accessorKey: "email",
    meta: {
      label: "Email",
    },
    header: "Email",
  },
  {
    id: "permission_level",
    meta: {
      label: "Acesso",
    },
    header: "Acesso",
    filterFn: (row, id, value) => {
      const permissionLevel = row.original.permission_level;
      return permissionLevel === value;
    },
    accessorFn: (row) =>
      getPermissionLabel(row.permission_level),
    size: 200,
    minSize: 200,
    cell: ({ row }) => {
      const permissionLevel = row.original.permission_level;
      const label = getPermissionLabel(permissionLevel);

      const badgeStyles: Record<PermissionLevel, string> = {
        [PermissionLevel.Admin]:
          "bg-violet-600 text-purple-100",
        [PermissionLevel.Manager]:
          "bg-blue-100 text-blue-600 border-blue-100",
        [PermissionLevel.User]:
          "bg-pink-100 text-pink-600 border-pink-100",
        [PermissionLevel.Viewer]: "",
        [PermissionLevel.Invited]: "",
      };

      return (
        <div className="flex justify-start">
          <Badge
            variant="outline"
            className={`rounded-full text-xxs font-medium whitespace-nowrap ${badgeStyles[permissionLevel]}`}
          >
            {label}
          </Badge>
        </div>
      );
    },
  },
  {
    accessorKey: "role",
    minSize: 200,
    meta: {
      label: "Cargo",
    },
    header: "Cargo",
    filterFn: (row, id, value) => {
      const role = row.getValue(id) as string;
      return role === value;
    },
    cell: ({ row }) => {
      const role = row.getValue("role") as string;
      return role ? <div>{role}</div> : <div className="text-gray-400">Cargo não definido</div>;
    },
  },
  {
    accessorKey: "mandato",
    size: 180,
    meta: {
      label: "Mandato",
    },
    header: "Mandato",
    cell: ({ row }) => {
      const mandatos = row.getValue("mandato") as Mandato[];
      if (mandatos && mandatos.length > 0) {
        return (
          <div onClick={(e) => e.stopPropagation()}>
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="link" className="text-brand-accent underline p-0 block min-w-0 max-w-full shrink text-left">
                  <span className="block truncate">{mandatos[0].nome_parlamentar}</span>
                </Button>
              </SheetTrigger>
              <SheetContent className={cn("!max-w-2xl !h-full !flex !flex-col")}>
                <Suspense fallback={<Spinner />}>
                  <ShowMandato mandato={mandatos[0]} />
                </Suspense>
              </SheetContent>
            </Sheet>
          </div>
        )
      }
      return <div className="text-gray-400">Sem mandato</div>;
    },
  },
  {
    accessorKey: "last_login",
    size: 150,
    meta: {
      label: "Último acesso"
    },
    header: ({ column, table }) => {
      return headerWithOrderBy(column, table);
    },
    cell: ({ row }) => {
      return getDateFromIso(row.getValue("last_login") as string) || <div className="text-gray-400">Sem registro</div>;
    },
  },
  {
    accessorKey: "is_active",
    meta: {
      label: "Status",
    },
    size: 100,
    header: "Status",
    cell: ({ row }) => {
      const isActive = row.getValue("is_active") as boolean;
      return <div>{isActive ? <Badge variant="success">Ativo</Badge> : <Badge variant="notice">Inativo</Badge>}</div>;
    },
  },
  {
    accessorKey: "created_at",
    size: 180,
    meta: {
      label: "Data de criação",
    },
    header: ({ column, table }) => {
      return headerWithOrderBy(column, table);
    },
    cell: ({ row }) => {
      const createdAt = row.getValue("created_at") as string;
      return createdAt ? <div>{getDateFromIso(createdAt)}</div> : <div className="text-gray-500">Não registrado</div>;
    },
  },
  {
    accessorKey: "actions",
    header: "",
    size: 100,
    meta: {
      label: "Ações",
    },
    cell: ({ row }) => {
      return <DeleteActionCell user={row.original} />;
    },
  },
];
