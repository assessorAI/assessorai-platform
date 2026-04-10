"use client";

import { Mandato } from "@/api/mandato/mandato.types";
import { UserResponse } from "@/api/user/user.types";
import { headerWithOrderBy } from "@/components/data-table/sort-button";
import { DeleteMandatoDialog } from "@/components/dialogs";
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Column, Row, Table } from "@tanstack/react-table";
import { TrashIcon } from "@heroicons/react/24/outline";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";
import { toast } from "sonner";
import { QueryClient, useQueryClient } from "@tanstack/react-query";
import { getDateFromIso } from "@/lib/get-date-from-iso";

function getGerenteMandato(mandato: (Mandato & { users: UserResponse[] })) {
  return mandato?.gerente?.[0]?.nome || <div className="text-gray-500">Não informado</div>;
}

const handleDelete = async (id: string, queryClient: QueryClient) => {
  try {
    await restClient(`/api/mandato/${id}`, {
      method: "DELETE",
    });

    // atualiza a lista de mandatos
    await queryClient.invalidateQueries({ queryKey: ["mandatos"] });

    toast.success("Mandato removido com sucesso");
  } catch (error) {
    const errorMessage = error as AppThrowError;
    toast.error(errorMessage.customMessage!);
  }
};

function DeleteActionCell({ mandato }: { mandato: Mandato }) {
  const queryClient = useQueryClient();

  return (
    <div onClick={(e) => e.stopPropagation()}>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="ghost" size="icon" className="size-4 hover:bg-destructive/10">
            <TrashIcon className="text-destructive" />
          </Button>
        </AlertDialogTrigger>
        <DeleteMandatoDialog
          name={mandato.nome_parlamentar}
          onConfirm={() => handleDelete(mandato.id.toString(), queryClient)}
          onCancel={() => { }}
        />
      </AlertDialog>
    </div>
  );
}


export const columns = [
  {
    accessorKey: "nome_parlamentar",
    minSize: 200,
    meta: {
      label: "Mandato",
    },
    header: ({ column, table }: { column: Column<Mandato>, table: Table<Mandato> }) => {
      return headerWithOrderBy(column, table);
    },
    cell: ({ row }: { row: Row<unknown> }) => {
      const nomeParlamentar = (row.original as (Mandato & { users: UserResponse[] })).nome_parlamentar;
      return nomeParlamentar ? <div>{nomeParlamentar}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "cargo_parlamentar",
    meta: {
      label: "Cargo do parlamentar",
    },
    header: "Cargo do parlamentar",
    size: 200,
    minSize: 200,
    cell: ({ row }: { row: Row<unknown> }) => {
      const cargo = (row.original as (Mandato & { users: UserResponse[] })).cargo_parlamentar;
      return cargo ? <div>{cargo}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "casa_legislativa",
    size: 250,
    meta: {
      label: "Casa Legislativa",
    },
    header: "Casa Legislativa",
    cell: ({ row }: { row: Row<unknown> }) => {
      const casa = (row.original as (Mandato & { users: UserResponse[] })).casa_legislativa;
      return casa ? <div>{casa}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "partido",
    size: 100,
    meta: {
      label: "Partido",
    },
    header: "Partido",
    cell: ({ row }: { row: Row<unknown> }) => {
      const partido = (row.original as (Mandato & { users: UserResponse[] })).partido;
      return partido ? <div>{partido}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "espectro_politico",
    meta: {
      label: "Posicionamento",
    },
    header: "Posicionamento",
    cell: ({ row }: { row: Row<unknown> }) => {
      const posicionamento = (row.original as (Mandato & { users: UserResponse[] })).espectro_politico;
      return posicionamento ? <div>{posicionamento}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "perfil_parlamentar",
    size: 120,
    meta: {
      label: "Perfil",
    },
    header: "Perfil",
    cell: ({ row }: { row: Row<unknown> }) => {
      const perfil = (row.original as (Mandato & { users: UserResponse[] })).perfil_parlamentar;
      return perfil ? <div>{perfil}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "municipio",
    meta: {
      label: "Município",
    },
    header: "Município",
    cell: ({ row }: { row: Row<unknown> }) => {
      const municipio = (row.original as (Mandato & { users: UserResponse[] })).municipio;
      return municipio ? <div>{municipio}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "ue",
    meta: {
      label: "UF",
    },
    header: "UF",
    size: 100,
    minSize: 100,
    cell: ({ row }: { row: Row<unknown> }) => {
      const ue = (row.original as (Mandato & { users: UserResponse[] })).ue;
      return ue ? <div>{ue}</div> : <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "gerente_mandato",
    size: 210,
    meta: {
      label: "Gerente do mandato",
    },
    header: "Gerente do mandato",
    cell: ({ row }: { row: Row<unknown> }) => {
      const gerente = getGerenteMandato(row.original as (Mandato & { users: UserResponse[] }));
      return gerente || <div className="text-gray-500">Não informado</div>;
    },
  },
  {
    accessorKey: "users",
    size: 180 ,
    meta: {
      label: "Número de membros",
    },
    header: "Número de membros",
    cell: ({ row }: { row: Row<unknown> }) => {
      const users = (row.original as (Mandato & { users: UserResponse[] })).users;
      return <div>{users.length}</div>;
    },
  },
  {
    accessorKey: "last_login",
    size: 150,
    meta: {
      label: "Último acesso"
    },
    header: ({ column, table }: { column: Column<Mandato>, table: Table<Mandato> }) => {
      return headerWithOrderBy(column, table);
    },
    cell: ({ row }: { row: Row<Mandato> }) => {
      const lastLogin = row.original.last_login;
      return lastLogin ? getDateFromIso(lastLogin.date) : <div className="text-gray-400">Sem registro</div>;
    },
  },
  {
    accessorKey: "created_at",
    size: 180,
    meta: {
      label: "Data de criação",
    },
    header: ({ column, table }: { column: Column<Mandato>, table: Table<Mandato> }) => {
      return headerWithOrderBy(column, table);
    },
    cell: ({ row }: { row: Row<unknown> }) => {
      const createdAt = (row.original as Mandato).created_at;
      return createdAt ? <div>{getDateFromIso(createdAt)}</div> : <div className="text-gray-500">Não registrado</div>;
    },
  },
  {
    accessorKey: "numero_atividades",
    size: 150,
    meta: {
      label: "N° de atividades",
    },
    header: "N° de atividades",
    cell: ({ row }: { row: Row<Mandato> }) => {
      return <div>{row.original.numero_atividades}</div>;
    },
  },
  {
    accessorKey: "actions",
    header: "",
    meta: {
      label: "Ações",
    },
    cell: ({ row }: { row: Row<Mandato> }) => {
      return <DeleteActionCell mandato={row.original} />;
    },
  },

];