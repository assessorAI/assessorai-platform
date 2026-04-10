import { Mandato } from "@/api/mandato/mandato.types";
import { restClient } from "@/lib/rest-client";

export const dadosMandatoService = {
  updateDadosMandato: async (mandato: Mandato) => {
    const body = {
      perfil_parlamentar: mandato.perfil_parlamentar,
      espectro_politico: mandato.espectro_politico,
      partido: mandato.partido,
      casa_legislativa: mandato.casa_legislativa,
      municipio: mandato.municipio,
      ue: mandato.ue,
      cargo_parlamentar: mandato.cargo_parlamentar,
      nome_parlamentar: mandato.nome_parlamentar,
    };

    const response = await restClient(`/api/mandato/${mandato.id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    });

    return response.json();
  }
};
