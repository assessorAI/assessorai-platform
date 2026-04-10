import { AnaliseConstitucionalidadeResponse } from "@/api/analise-constitucionalidade/analise-constitucionalidade.types";
import { analiseConstitucionalidadeService } from "@/features/analise-constitucionalidade/analise-constitucionalidade.service";
import { useMandato } from "@/hooks/useMandato";
import { useCallback, useState } from "react";
import { AppThrowError } from "@/api/error/app-throw-error";

export const useHandleAnaliseConstitucionalidadeRequest = () => {
  const mandato = useMandato();
  const [isLoading, setIsLoading] = useState(false);
  const [analiseConstitucionalidade, setAnaliseConstitucionalidade] =
    useState<AnaliseConstitucionalidadeResponse | null>(null);
  const [errorAnaliseConstitucionalidade, setErrorAnaliseConstitucionalidade] =
    useState<string | null>(null);

  const onReceiveAnaliseConstitucionalidade = useCallback(
    (data: AnaliseConstitucionalidadeResponse) => {
      setAnaliseConstitucionalidade(data);
    },
    []
  );

  const onErrorAnaliseConstitucionalidade = useCallback((error: string) => {
    setErrorAnaliseConstitucionalidade(error);
  }, []);

  const handleAnaliseConstitucionalidadeRequest = useCallback(
    async (file: File) => {

      if (!mandato) {
        setErrorAnaliseConstitucionalidade("Mandato não encontrado");
        return;
      }

      setIsLoading(true);
      setErrorAnaliseConstitucionalidade(null);
      setAnaliseConstitucionalidade(null);

      try {
        const data =
          await analiseConstitucionalidadeService.analisarConstitucionalidade({
            file,
          }, mandato.id.toString());

        onReceiveAnaliseConstitucionalidade(data);
      } catch (error) {
        const errorMessage = error as AppThrowError;
        onErrorAnaliseConstitucionalidade(errorMessage.customMessage!);
      } finally {
        setIsLoading(false);
      }
    },
    [onReceiveAnaliseConstitucionalidade, mandato, onErrorAnaliseConstitucionalidade]
  );

  return {
    isLoading,
    handleAnaliseConstitucionalidadeRequest,
    analiseConstitucionalidade,
    errorAnaliseConstitucionalidade,
  };
};
