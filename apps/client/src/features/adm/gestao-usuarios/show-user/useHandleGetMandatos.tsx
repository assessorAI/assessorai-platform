"use client";

import { AppThrowError } from "@/api/error/app-throw-error";
import { MandatosResponse } from "@/api/mandato/mandato.types";
import { useCallback, useState } from "react";
import { restClient } from "@/lib/rest-client";

export const useHandleGetMandatos = () => {
  const [mandatos, setMandatos] = useState<MandatosResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGetMandatos = useCallback(async (signal: AbortSignal) => {
    setIsLoading(true);
    setError(null);
    setMandatos(null);

    try {
      const response = await restClient("/api/mandatos", { signal });
      const data = await response.json();
      setMandatos(data as MandatosResponse);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      const errorMessage = error as AppThrowError;
      setError(errorMessage.customMessage!);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    mandatos,
    handleGetMandatos,
    isLoading,
    error,
  };
};
