import { ArrowDownTrayIcon } from "@heroicons/react/24/solid";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";

export function DownloadDocumentoCasa({
  id,
  filename,
}: {
  id: string;
  filename: string;
}) {
  const handleDownload = async () => {
    try {
      const response = await restClient(`/api/documentos-casa/${id}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Arquivo baixado com sucesso");
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    }
  };

  return (
    <DropdownMenuItem onClick={handleDownload}>
      <ArrowDownTrayIcon className="w-4 h-4" />
      Baixar arquivo
    </DropdownMenuItem>
  );
}
