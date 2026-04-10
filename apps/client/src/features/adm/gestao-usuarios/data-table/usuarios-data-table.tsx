"use client";

import { DataTable } from "@/components/data-table/data-table";
import { UserResponse } from "@/api/user/user.types";
import { columns } from "./columns";
import { Filters } from "./filters";
import { ShowUser } from "../show-user/show-user";
import { Row } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import GestaoUsuariosLoading from "@/app/(adm)/adm/gestao-usuarios/loading";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";
import { toast } from "sonner";
import { AddUserDialog } from "./add-user-dialog";
import { NovoUsuario } from "../novo-usuario/novo-usuario";
import { NovoMandatoStep } from "../../gestao-mandatos/novo-mandato/novo-mandato-step";
import { DateRange } from "react-day-picker";

export function UsersDataTable() {
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<string[]>([]);
  const [permission_level, setPermissionLevel] = useState<string[]>([]);
  const [orderBy, setOrderBy] = useState("");
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  const limit = 10;
  const offset = page * limit;

  const handleSearchChange = useCallback((newSearch: string) => {
    setSearch(newSearch);
    setPage(0);
  }, []);

  const handleDateRangeChange = useCallback((newDateRange: DateRange | undefined) => {
    setDateRange(newDateRange);
    setPage(0);
  }, []);

  const handleRoleChange = useCallback((newRole: string[]) => {
    setRole(newRole);
    setPage(0);
  }, []);

  const handlePermissionChange = useCallback((newPermission: string[]) => {
    setPermissionLevel(newPermission);
    setPage(0);
  }, []);

  const handleOrderByChange = useCallback((newOrderBy: string) => {
    setOrderBy(newOrderBy);
    setPage(0);
  }, []);

  const handleMandatoExistente = useCallback(() => {
    return <NovoUsuario />; 
  }, []);

  const handleNovoMandato = useCallback(() => {
    return <NovoMandatoStep />;
  }, []);

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["users", page, limit, search, role, permission_level, orderBy, dateRange],
    queryFn: async () => {
      const searchParam = search ? `&search=${encodeURIComponent(search)}` : "";
      const roleParam = role.length > 0 ? `&role=${encodeURIComponent(role.join(","))}` : "";
      const permissionParam = permission_level.length > 0 ? `&permission_level=${encodeURIComponent(permission_level.join(","))}` : ""; 
      const orderByParam = orderBy ? `&orderBy=${encodeURIComponent(orderBy)}` : "";
      const dateRangeParam = dateRange ? `&from=${encodeURIComponent(dateRange.from?.toISOString() || "")}&to=${encodeURIComponent(dateRange.to?.toISOString() || "")}` : "";

      const response = await restClient(
        `/api/users?limit=${limit}&offset=${offset}${searchParam}${roleParam}${permissionParam}${orderByParam}${dateRangeParam}`
      );
      return response.json();
    },
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return <GestaoUsuariosLoading />;
  }

  if (error) {
    const errorMessage = error as AppThrowError;
    toast.error(errorMessage.customMessage);
  }

  const totalPages = Math.ceil((data?.total || 0) / limit);

  return (
    <DataTable
      orderBy={orderBy}
      isFetching={isFetching}
      onOrderByChange={handleOrderByChange}
      columns={columns}
      data={data?.users || []}
      totalPages={totalPages}
      pageIndex={page}
      pageSize={limit}
      onPaginationChange={setPage}
      searchValue={search}
      newDataForm={
        <AddUserDialog 
          onMandatoExistente={handleMandatoExistente} 
          onNovoMandato={handleNovoMandato} />
      }
      onSearchChange={handleSearchChange}
      sheetContent={(row: Row<UserResponse>) => (
        <ShowUser user={row.original} />
      )}
      filters={() => (
        <Filters
          role={role}
          permission_level={permission_level}
          dateRange={dateRange}
          onDateRangeChange={handleDateRangeChange}
          onRoleChange={handleRoleChange}
          onPermissionChange={handlePermissionChange}
        />
      )}
    />
  );
}