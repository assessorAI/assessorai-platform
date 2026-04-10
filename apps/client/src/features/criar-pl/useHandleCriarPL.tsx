import { useState } from "react";
import { criarPLService } from "./criar-pl.service";
import { CriarPLResponse } from "@/api/criar-pl/criar-pl.types";
import { useMandato } from "@/hooks/useMandato";
import { AppThrowError } from "@/api/error/app-throw-error";

export const useHandleCriarPL = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projetoLei, setProjetoLei] = useState<CriarPLResponse | null>(null);
  const mandato = useMandato();

  const handleCriarPL = async (text: string, files?: File[]) => {
    setIsLoading(true);
    setError(null);
    setProjetoLei(null);

    try {
      const response = await criarPLService.criarPL(text, mandato!.id.toString(), files);

      setProjetoLei(response);
    } catch (error) {
      const errorMessage = error as AppThrowError;
      setError(errorMessage.customMessage!);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    handleCriarPL,
    projetoLei,
    isLoading,
    error,
  };
};
