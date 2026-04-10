import { convertFileToContentJson } from "@/lib/convert-file-to-json";
import { RequerimentoResponse } from "@/api/requerimento/requerimento.types";
import { restClient } from "@/lib/rest-client";

export const requerimentoService = {
    criarRequerimento: async (text: string, mandatoId: string, files?: File[]): Promise<RequerimentoResponse> => {
      const params = new URLSearchParams();
      params.append("input", text);
      const hasFiles = Array.isArray(files) && files.length > 0;
  
      if (hasFiles) {
        const referencias = await Promise.all(
          files.map(async (file) => {
            return convertFileToContentJson(file);
          })
        );
  
        params.append("referencias", JSON.stringify(referencias));
      } 
  
      const res = await restClient(`/api/requerimento/${mandatoId}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params.toString(),
      });
  
      return res.json();
    }
}