import { Skeleton } from "../ui/skeleton";

export function GridLoading({ count }: { count: number }) {
  return (
    <div className="grid grid-cols-3 gap-8">
      {Array.from({ length: count }).map((_, index) => (
        <div
          className="flex flex-col space-y-3 border border-gray-200 rounded-lg p-4 w-full bg-white"
          key={index}
        >
          <Skeleton className="h-4 w-[100px]" />
          <Skeleton className="h-4 w-[200px]" />
          <Skeleton className="h-4 w-[250px]" />
          <Skeleton className="h-4 w-[200px]" />
        </div>
      ))}
    </div>
  );
}
