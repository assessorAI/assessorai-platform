import { CriarPLResponse } from "@/api/criar-pl/criar-pl.types";
import { convertFileToContentJson } from "@/lib/convert-file-to-json";
import { restClient } from "@/lib/rest-client";

export const criarPLService = {
  criarPL: async (text: string, mandatoId: string, files?: File[]): Promise<CriarPLResponse> => {
    const params = new URLSearchParams();
    params.append("text", text);
    const hasFiles = Array.isArray(files) && files.length > 0;

    if (hasFiles) {
      const referencias = await Promise.all(
        files.map(async (file) => {
          return convertFileToContentJson(file);
        })
      );

      params.append("referencias", JSON.stringify(referencias));
    } 

    const res = await restClient(`/api/criar-pl/${mandatoId}`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    });

    return res.json();
  },
};

