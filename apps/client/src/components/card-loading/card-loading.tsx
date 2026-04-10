import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function CardLoading({ noBorder = false }: { noBorder?: boolean }) {
  return (
    <Card className={cn("w-full", noBorder && "border-none")}>
      <CardHeader>
        <CardTitle>
          <Skeleton className="h-6 w-[180px]" />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  );
}
