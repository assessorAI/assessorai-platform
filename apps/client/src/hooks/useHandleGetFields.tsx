import { useState } from "react";
import { Municipio, UF } from "@/api/gov/api-gov.types";
import { getFieldsService } from "../lib/get-fields.service";

export const useHandleBuscaCampos = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ufList, setUfList] = useState<UF[]>([]);
  const [municipioList, setMunicipioList] = useState<Municipio[]>([]);

  const handleBuscaUF = async () => {
    setIsLoading(true);
    setError(null);
    setUfList([]);

    try {
      const response = await getFieldsService.buscarUFs();
      setUfList(response as UF[]);

    } catch (error) {
      setError(error instanceof Error ? error.message : "Erro desconhecido");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBuscaMunicipios = async (uf: string) => {
    setIsLoading(true);
    setError(null);
    setMunicipioList([]);
  
    try {
      const response = await getFieldsService.getMunicipios(uf);
      setMunicipioList(response as Municipio[]);
  
    } catch (error) {
      setError(error instanceof Error ? error.message : "Erro desconhecido");
    } finally {
      setIsLoading(false);
    }
  };

  const getCasaLegislativa = (cargo: string, uf: string, municipio: string) => {
    return getFieldsService.getCasaLegislativa(cargo, uf, municipio);
  }

  return {
    handleBuscaUF,
    handleBuscaMunicipios,
    ufList,
    municipioList,
    getCasaLegislativa,
    isLoading,
    error,
  };
};
