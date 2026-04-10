import { apiClient } from "../api-client";
import { ENDPOINTS } from "@/config/endpoints";
import { Mandato, MandatosResponse, MandatoUsersResponse } from "./mandato.types";
import {
  DocumentosCasaFileType,
  DocumentosCasaResponse,
} from "@/types/documentos-casa.types";

export const mandatoService = {
  getMandatos: async () => {
    return await apiClient.get<MandatosResponse>(
      ENDPOINTS.MANDATO.GET_ALL
    );
  },
  getMandato: async (id: string) => {
    return await apiClient.get<Mandato>(
      ENDPOINTS.MANDATO.GET.replace("{id}", id)
    );
  },
  getMandatoDocuments: async (mandatoId: string) => {
    const file_types = Object.values(DocumentosCasaFileType).join(",");

      return await apiClient.get<DocumentosCasaResponse>(
      ENDPOINTS.MANDATO.GET_DOCUMENTS,
      {
        params: {
          mandato_id: mandatoId,
          file_types,
        },
      }
    );
  },
  getMandatoUsers: async (mandatoId: string) => {
    return await apiClient.get<MandatoUsersResponse>(
      ENDPOINTS.MANDATO.USERS.replace("{mandato_id}", mandatoId)
    );
  },
};
