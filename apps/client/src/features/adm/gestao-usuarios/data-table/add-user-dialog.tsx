import { useState } from "react";
import { BuildingLibraryIcon, PlusIcon, UserPlusIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";

type AddUserDialogProps = {
    onMandatoExistente?: () => React.ReactNode;
    onNovoMandato?: () => React.ReactNode;
};

export function AddUserDialog({ onMandatoExistente, onNovoMandato }: AddUserDialogProps) {
    const [open, setOpen] = useState(false);
    const [dialogContent, setDialogContent] = useState<React.ReactNode>(null);

    const handleMandatoExistente = () => {
        const content = onMandatoExistente?.();
        setDialogContent(content ?? null);
        setOpen(true);
    };

    const handleNovoMandato = () => {
        const content = onNovoMandato?.();
        setDialogContent(content ?? null);
        setOpen(true);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon" aria-label="Adicionar usuário">
                        <PlusIcon className="size-4" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="min-w-[16rem]">
                    <DropdownMenuItem onSelect={handleMandatoExistente}>
                        <UserPlusIcon className="size-4" />
                        Criar usuário em um mandato existente
                    </DropdownMenuItem>
                    <DropdownMenuItem onSelect={handleNovoMandato}>
                        <BuildingLibraryIcon className="size-4" />
                        Criar usuário em um novo mandato
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
            <DialogContent className="px-10 py-16">
                <VisuallyHidden>
                    <DialogTitle>Adicionar usuário</DialogTitle>
                </VisuallyHidden>
                {dialogContent}
            </DialogContent>
        </Dialog>
    );
}