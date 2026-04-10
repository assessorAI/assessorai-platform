"use client";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  Row,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";

import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { DataTableViewOptions } from "./column-toggle";

import { Suspense, useState, useEffect } from "react";
import { Table as TanStackTable } from "@tanstack/react-table";
import {
  Sheet,
  SheetContent,
} from "../ui/sheet";
import { cn } from "@/lib/utils";
import { Spinner } from "../ui/spinner";
import { DataTableBody } from "./data-table-body";
import { DataTableLoading } from "./data-table-loading";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  filters?: (table: TanStackTable<TData>) => React.ReactNode;
  sheetContent?: (row: Row<TData>) => React.ReactNode;
  pageIndex: number;
  pageSize: number;
  onPaginationChange: (pageIndex: number) => void;
  totalPages: number;
  newDataForm?: React.ReactNode;
  searchValue: string;
  onSearchChange: (search: string) => void;
  orderBy: string;
  onOrderByChange: (orderBy: string) => void;
  isFetching: boolean;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  filters,
  sheetContent,
  onPaginationChange,
  pageIndex,
  pageSize,
  totalPages,
  newDataForm,
  searchValue,
  onSearchChange,
  orderBy,
  onOrderByChange,
  isFetching,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [openRow, setOpenRow] = useState<Row<TData> | null>(null);
  // Estado local para o input (atualização imediata)
  const [inputValue, setInputValue] = useState(searchValue);

  // Sincroniza inputValue quando searchValue mudar externamente
  useEffect(() => {
    setInputValue(searchValue);
  }, [searchValue]);

  // Debounce: aguarda 500ms após parar de digitar
  useEffect(() => {
    const timer = setTimeout(() => {
      // Só chama onSearchChange se o valor for diferente
      if (inputValue !== searchValue) {
        onSearchChange(inputValue);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [inputValue, searchValue, onSearchChange]);

  const table = useReactTable({
    data,
    columns,
    meta: {
      isLoading: isFetching,
      orderBy,
      onOrderByChange,
    },
    state: {
      sorting,
      pagination: {
        pageIndex,
        pageSize,
      },
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    defaultColumn: {
      size: 150,
      minSize: 100,
    },
    onPaginationChange: (updater) => {
      const next =
        typeof updater === "function"
          ? updater({ pageIndex, pageSize })
          : updater;

      onPaginationChange(next.pageIndex);
    },
    manualPagination: true,
    manualSorting: true,
    pageCount: totalPages,
  });

  // Atualiza apenas o estado local do input
  const handleInputChange = (value: string) => {
    setInputValue(value);
  };

  // Limpa a busca imediatamente
  const handleClearSearch = () => {
    setInputValue("");
    onSearchChange("");
  };

  return (
    <div>
      <Sheet open={!!openRow} onOpenChange={() => setOpenRow(null)}>
        <SheetContent className={cn("!max-w-2xl !h-full !flex !flex-col")}>
          <Suspense fallback={<Spinner />}>
            {sheetContent && openRow && sheetContent(openRow)}
          </Suspense>
        </SheetContent>
      </Sheet>
      {/* Filtros */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <Input
            placeholder="Busca"
            value={inputValue}
            onChange={(e) => handleInputChange(e.target.value)}
            className="w-full bg-white"
          />

          {inputValue && (
            <Button variant="link" onClick={handleClearSearch}>
              Limpar busca
            </Button>
          )}
          {newDataForm}
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {filters && (
            <div className="flex items-center gap-3 py-2 mb-2">
              {filters(table)}
            </div>
          )}

          <DataTableViewOptions table={table} />
        </div>
      </div>

      {/* Tabela */}
      <div className="overflow-x-auto rounded-md border mt-4">
        <Table className="bg-white table-fixed w-full">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    style={{ width: header.getSize() }}
                    className="truncate px-4"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>

          <TableBody>
            {isFetching ? (
              <DataTableLoading columnsLength={columns.length} rowCount={pageSize} />
            ) : (
              <DataTableBody
                table={table}
                columnsLength={columns.length}
                onRowClick={setOpenRow}
              />
            )}
          </TableBody>
        </Table>
      </div>

      {/* Paginação */}
      <div className="flex items-center justify-end space-x-2 py-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Anterior
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Próxima
        </Button>
      </div>
    </div>
  );
}