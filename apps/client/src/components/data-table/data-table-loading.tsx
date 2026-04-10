import { TableCell, TableRow } from "../ui/table";
import { Skeleton } from "../ui/skeleton";

interface DataTableLoadingProps {
  columnsLength: number;
  rowCount?: number;
}

export function DataTableLoading({ 
  columnsLength, 
  rowCount = 10 
}: DataTableLoadingProps) {
  return (
    <>
      {Array.from({ length: rowCount }).map((_, rowIndex) => (
        <TableRow key={rowIndex}>
          {Array.from({ length: columnsLength }).map((_, colIndex) => (
            <TableCell
              key={colIndex}
              className="px-5 py-3"
            >
              <Skeleton className="h-5 w-full" />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}