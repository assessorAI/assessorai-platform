import { flexRender, Table as TanStackTable, Row } from "@tanstack/react-table";
import { TableCell, TableRow } from "../ui/table";

interface DataTableBodyProps<TData> {
  table: TanStackTable<TData>;
  onRowClick?: (row: Row<TData>) => void;
  columnsLength: number;
}

export function DataTableBody<TData>({ 
  table, 
  onRowClick,
  columnsLength 
}: DataTableBodyProps<TData>) {
  return (
    <>
      {table.getRowModel().rows.length ? (
        table.getRowModel().rows.map((row) => (
          <TableRow
            key={row.id}
            onClick={() => onRowClick?.(row)}
            data-state={row.getIsSelected() && "selected"}
            className="cursor-pointer hover:bg-muted transition-colors"
          >
            {row.getVisibleCells().map((cell) => (
              <TableCell
                key={cell.id}
                style={{ width: cell.column.getSize() }}
                className="text-black px-4 py-3 truncate"
              >
                {flexRender(
                  cell.column.columnDef.cell,
                  cell.getContext()
                )}
              </TableCell>
            ))}
          </TableRow>
        ))
      ) : (
        <TableRow>
          <TableCell
            colSpan={columnsLength}
            className="h-24 text-center"
          >
            No results.
          </TableCell>
        </TableRow>
      )}
    </>
  );
}