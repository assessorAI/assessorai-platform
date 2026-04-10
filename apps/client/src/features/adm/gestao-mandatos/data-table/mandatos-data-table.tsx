"use client";

import { DataTable } from "@/components/data-table/data-table";
import { columns } from "./columns";
import { ColumnDef, Row } from "@tanstack/react-table";
import { Filters } from "./filters";
import { useQuery } from "@tanstack/react-query";
import { restClient } from "@/lib/rest-client";
import { useCallback, useState } from "react";
import { toast } from "sonner";
import GestaoMandatosLoading from "@/app/(adm)/adm/gestao-mandatos/loading";
import { ShowMandato } from "../show-mandato/show-mandato";
import { Mandato } from "@/api/mandato/mandato.types";
import { NovoMandato } from "../novo-mandato/novo-mandato";
import { AddDialog } from "@/components/data-table/add-dialog";
import { DateRange } from "react-day-picker";

export function MandatosDataTable() {
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [cargo_parlamentar, setCargoParlamentar] = useState<string[]>([]);
  const [casa_legislativa, setCasaLegislativa] = useState<string[]>([]);
  const [partido, setPartido] = useState<string[]>([]);
  const [perfil_parlamentar, setPerfilParlamentar] = useState<string[]>([]);
  const [espectro_politico, setEspectroPolitico] = useState<string[]>([]);
  const [orderBy, setOrderBy] = useState("");
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);

  const limit = 10;
  const offset = page * limit;

  const handleOrderByChange = useCallback((newOrderBy: string) => {
    setOrderBy(newOrderBy);
    setPage(0);
  }, []);

  const handleDateRangeChange = useCallback((newDateRange: DateRange | undefined) => {
    setDateRange(newDateRange);
    setPage(0);
  }, []);

  const handleSearchChange = useCallback((newSearch: string) => {
    setSearch(newSearch);
    setPage(0);
  }, []);

  const handleCargoParlamentarChange = useCallback((newCargo: string[]) => {
    setCargoParlamentar(newCargo);
    setPage(0);
  }, []);

  const handleCasaLegislativaChange = useCallback((newCasa: string[]) => {
    setCasaLegislativa(newCasa);
    setPage(0);
  }, []);

  const handlePartidoChange = useCallback((newPartido: string[]) => {
    setPartido(newPartido);
    setPage(0);
  }, []);

  const handlePerfilParlamentarChange = useCallback((newPerfil: string[]) => {
    setPerfilParlamentar(newPerfil);
    setPage(0);
  }, []);

  const handleEspectroPoliticoChange = useCallback((newEspectro: string[]) => {
    setEspectroPolitico(newEspectro);
    setPage(0);
  }, []);

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: [
      "mandatos", 
      page, limit, search, 
      cargo_parlamentar, 
      casa_legislativa, 
      partido, 
      perfil_parlamentar, 
      espectro_politico, 
      orderBy, 
      dateRange
    ],
    queryFn: async () => {
      try {
        const searchParam = search ? `&search=${encodeURIComponent(search)}` : "";
        const cargoParam = cargo_parlamentar ? `&cargo_parlamentar=${encodeURIComponent(cargo_parlamentar.join(","))}` : "";
        const casaParam = casa_legislativa ? `&casa_legislativa=${encodeURIComponent(casa_legislativa.join(","))}` : "";
        const partidoParam = partido ? `&partido=${encodeURIComponent(partido.join(","))}` : "";
        const perfilParam = perfil_parlamentar ? `&perfil_parlamentar=${encodeURIComponent(perfil_parlamentar.join(","))}` : "";
        const espectroParam = espectro_politico ? `&espectro_politico=${encodeURIComponent(espectro_politico.join(","))}` : "";
        const orderByParam = orderBy ? `&orderBy=${encodeURIComponent(orderBy)}` : "";
        const dateRangeParam = dateRange ? `&from=${encodeURIComponent(dateRange.from?.toISOString() || "")}&to=${encodeURIComponent(dateRange.to?.toISOString() || "")}` : "";


        const response = await restClient(
          `/api/mandatos?limit=${limit}&offset=${offset}${searchParam}${cargoParam}${casaParam}${partidoParam}${perfilParam}${espectroParam}${orderByParam}${dateRangeParam}`
        );

        return response.json();
      } catch (error) {
        throw error;
      }
    },
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) return <GestaoMandatosLoading />;
  if (error) return toast.error(error.message);

  const totalPages = Math.ceil((data?.total || 0) / limit);

  return (
    <DataTable
      columns={columns as ColumnDef<Mandato, unknown>[]}
      data={data?.mandatos || []}
      isFetching={isFetching}
      orderBy={orderBy}
      onOrderByChange={handleOrderByChange}
      searchValue={search}
      onSearchChange={handleSearchChange}
      totalPages={totalPages}
      pageIndex={page}
      pageSize={limit}
      onPaginationChange={setPage}
      newDataForm={
        <AddDialog>
          <NovoMandato />
        </AddDialog>
      }
      sheetContent={(row: Row<Mandato>) => (
        <ShowMandato mandato={row.original} />
      )}
      filters={() => 
        <Filters
        cargo_parlamentar={cargo_parlamentar}
        casa_legislativa={casa_legislativa}
        partido={partido}
        perfil_parlamentar={perfil_parlamentar}
        espectro_politico={espectro_politico}
        dateRange={dateRange}
        onDateRangeChange={handleDateRangeChange}
        onCargoParlamentarChange={handleCargoParlamentarChange}
        onCasaLegislativaChange={handleCasaLegislativaChange}
        onPartidoChange={handlePartidoChange}
        onPerfilParlamentarChange={handlePerfilParlamentarChange}
        onEspectroPoliticoChange={handleEspectroPoliticoChange}
      />
      }
    />
  );
}
