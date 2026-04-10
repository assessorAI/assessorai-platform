import { ENDPOINTS } from "@/config/endpoints";
import { apiClient } from "../api-client";
import { AdmSummaryResponse } from "./adm.types";

export const admService = {
  summary: async () => {
    return await apiClient.get<AdmSummaryResponse>(ENDPOINTS.ADM.SUMMARY);
  },
};