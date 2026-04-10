import { useState } from "react";
import { useMandato } from "@/hooks/useMandato";
import { RequerimentoResponse } from "@/api/requerimento/requerimento.types";
import { requerimentoService } from "./requerimento.service";
import { AppThrowError } from "@/api/error/app-throw-error";

export const useHandleRequerimento = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requerimento, setRequerimento] = useState<RequerimentoResponse | null>(null);
  const mandato = useMandato();

  const handleRequerimento = async (text: string, files?: File[]) => {
    setIsLoading(true);
    setError(null);
    setRequerimento(null);

    try {
      const response = await requerimentoService.criarRequerimento(text, mandato!.id.toString(), files);
      setRequerimento(response);
    } catch (error) {
      const errorMessage = error as AppThrowError;
      setError(errorMessage.customMessage!);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    handleRequerimento,
    requerimento,
    isLoading,
    error,
  };
};
