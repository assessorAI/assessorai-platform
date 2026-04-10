import { ProjetoReferencia } from "@/context/projetos-referencias.context";
import { restClient } from "@/lib/rest-client";

export const buscaReferenciasService = {
  buscarReferencias: async (tema: string, offset?: number): Promise<ProjetoReferencia[]> => {

    const res = await restClient(`/api/busca-referencias?tema=${tema}&offset=${offset}`, { method: "GET" });

    return res.json();
  },
};