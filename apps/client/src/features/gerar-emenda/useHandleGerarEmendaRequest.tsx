import { CreateEmendaResponse } from "@/api/emenda/emenda.types";
import { Emenda } from "@/api/emenda/emenda.types";
import { useMandato } from "@/hooks/useMandato";
import { useCallback, useState } from "react";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";

export function useHandleGerarEmendaRequest(
  onSuccess: (data: CreateEmendaResponse) => void,
  onError: (error: string) => void
) {
  const [isLoading, setIsLoading] = useState(false);
  const mandato = useMandato();
  const handleGerarEmendaRequest = useCallback(
    async (emendaSelecionada: Emenda, file: File) => {
      setIsLoading(true);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("art", emendaSelecionada.art.toString());
      formData.append("tipo", emendaSelecionada.tipo);
      formData.append("texto", emendaSelecionada.texto);

      try {
        const response = await restClient(
          `/api/emenda/${mandato!.id.toString()}`,
          {
            method: "POST",
            body: formData,
          }
        );

        const data = await response.json();
        onSuccess(data);
      } catch (error) {
        const errorMessage = error as AppThrowError;
        onError(errorMessage.customMessage!);
      } finally {
        setIsLoading(false);
      }
    },
    [onSuccess, onError, mandato]
  );

  return {
    isLoading,
    handleGerarEmendaRequest,
  };
}
