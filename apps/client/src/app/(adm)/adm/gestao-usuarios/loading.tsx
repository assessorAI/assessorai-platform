import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

export default function GestaoUsuariosLoading() {
  return (
    <section>
      <div>
        <div className="flex flex-col gap-4">
          {/* Skeleton do campo de busca */}
          <Skeleton className="h-10 w-full" />

          {/* Skeleton dos filtros */}
          <div className="flex items-center gap-3 py-2 mb-2">
            <Skeleton className="h-10 w-[200px]" />
            <Skeleton className="h-10 w-[200px]" />
            <Skeleton className="h-10 w-[200px]" />
          </div>
        </div>

        {/* Skeleton da tabela */}
        <div className="overflow-hidden rounded-md border mt-4">
          <Table className="bg-white">
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Skeleton className="h-4 w-16" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-12" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-16" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-16" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-20" />
                </TableHead>
                <TableHead>
                  {/* Coluna de ações sem header */}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-48" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-6 w-24 rounded-full" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-28" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-36" />
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Skeleton className="h-8 w-8 rounded" />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Skeleton da paginação */}
        <div className="flex items-center justify-end space-x-2 py-4">
          <Button variant="outline" size="sm" disabled>
            <Skeleton className="h-4 w-16" />
          </Button>
          <Button variant="outline" size="sm" disabled>
            <Skeleton className="h-4 w-16" />
          </Button>
        </div>
      </div>
    </section>
  );
}

