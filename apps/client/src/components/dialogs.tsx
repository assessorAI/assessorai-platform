import {
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";

export function AdmAlertDialog({ name, onConfirm, onCancel }: { name: string, onConfirm: () => void, onCancel: () => void }) {
  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Esse usuário será um administrador.</AlertDialogTitle>
        <AlertDialogDescription>
          Tem certeza que deseja transformar o usuário {name} em administrador?
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={onCancel}>Cancelar</AlertDialogCancel>
        <AlertDialogAction onClick={onConfirm}>Confirmar</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  );
}

export function SalvarAlteracoesDialog({ onConfirm, onCancel }: { onConfirm: () => void, onCancel: () => void }) {
  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Deseja salvar as alterações?</AlertDialogTitle>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={onCancel}>Cancelar</AlertDialogCancel>
        <AlertDialogAction onClick={onConfirm}>Confirmar</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  );
}

export function DescartarAlteracoesDialog({ onConfirm, onCancel }: { onConfirm: () => void, onCancel: () => void }) {
  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>
          Deseja descartar as alterações feitas?
        </AlertDialogTitle>
      </AlertDialogHeader>
      <AlertDialogDescription>
        Essa ação não poderá ser desfeita.
      </AlertDialogDescription>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={onCancel}>Cancelar</AlertDialogCancel>
        <AlertDialogAction onClick={onConfirm}>Confirmar</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  );
}


export function DeleteUserDialog({ name, onConfirm, onCancel }: { name: string, onConfirm: () => void, onCancel: () => void }) {
  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Tem certeza que deseja remover o usuário {name}?</AlertDialogTitle>
        <AlertDialogDescription>
          Essa ação não poderá ser desfeita.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={onCancel}>Cancelar</AlertDialogCancel>
        <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={onConfirm}>Remover</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent> 
  );
}

export function DeleteMandatoDialog({ name, onConfirm, onCancel }: { name: string, onConfirm: () => void, onCancel: () => void }) {
  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Tem certeza que deseja remover o mandato {name}?</AlertDialogTitle>
        <AlertDialogDescription>
          Essa ação não poderá ser desfeita.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={onCancel}>Cancelar</AlertDialogCancel>
        <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={onConfirm}>Remover</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent> 
  );
}