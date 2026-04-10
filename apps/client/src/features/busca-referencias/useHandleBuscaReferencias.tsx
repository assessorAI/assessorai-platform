import { useState } from "react";

import { buscaReferenciasService } from "./busca-referencias.service";
import { ProjetoReferencia } from "@/context/projetos-referencias.context";
import { AppThrowError } from "@/api/error/app-throw-error";

export const useHandleBuscaReferencias = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [referencias, setReferencias] =
    useState<ProjetoReferencia[] | null>(null);

  const handleBuscarReferencias = async (tema: string, offset: number = 0) => {
    setIsLoading(true);
    setError(null);
    setReferencias(null);

    try {
      const response = await buscaReferenciasService.buscarReferencias(tema, offset);
      setReferencias(response);
    } catch (error) {
      const errorMessage = error as AppThrowError;
      setError(errorMessage.customMessage!);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    handleBuscarReferencias,
    referencias,
    isLoading,
    error,
  };
};
