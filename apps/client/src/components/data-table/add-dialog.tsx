import { PlusIcon } from "@heroicons/react/24/outline";
import { Button } from "../ui/button";
import { Dialog, DialogTrigger } from "../ui/dialog";

export function AddDialog({ children }: { children: React.ReactNode }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <PlusIcon className="size-4" />
        </Button>
      </DialogTrigger>
        {children}
    </Dialog>
  );
}