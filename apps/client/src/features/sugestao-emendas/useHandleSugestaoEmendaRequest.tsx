import { AppThrowError } from "@/api/error/app-throw-error";
import { SugestaoEmendasResponse } from "@/api/sugestao-emendas/sugestao-emendas.types";
import { useMandato } from "@/hooks/useMandato";
import { restClient } from "@/lib/rest-client";
import { useCallback, useState } from "react";

export const useHandleSugestaoEmendaRequest = () => {
  const mandato = useMandato();
  const [isLoading, setLoading] = useState<boolean>(false);
  const [sugestoesEmendas, setSugestoesEmendas] =
    useState<SugestaoEmendasResponse>({
      emendas: [],
    });
  const [errorSugestaoEmenda, setErrorSugestaoEmenda] = useState<string | null>(
    null
  );

  const onReceiveSugestaoEmenda = useCallback(
    (data: SugestaoEmendasResponse) => {
      setSugestoesEmendas(data);
    },
    []
  );

  const onErrorSugestaoEmenda = useCallback((error: string) => {
    setErrorSugestaoEmenda(error);
  }, []);

  const handleSugestaoEmendaRequest = useCallback(
    async (file: File) => {
      setLoading(true);
      setErrorSugestaoEmenda(null);
      setSugestoesEmendas({
        emendas: [],
      });

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await restClient(`/api/sugestao-emendas/${mandato!.id.toString()}`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        onReceiveSugestaoEmenda(data);
      } catch (error) {
        const errorMessage = error as AppThrowError;
        onErrorSugestaoEmenda(errorMessage.customMessage!);
      } finally {
        setLoading(false);
      }
    },
    [onReceiveSugestaoEmenda, mandato, onErrorSugestaoEmenda]
  );

  return {
    isLoading,
    sugestoesEmendas,
    errorSugestaoEmenda,
    handleSugestaoEmendaRequest,
  };
};
