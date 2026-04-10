import {
  AnaliseConstitucionalidadeRequest,
  AnaliseConstitucionalidadeResponse,
} from "@/api/analise-constitucionalidade/analise-constitucionalidade.types";
import { restClient } from "@/lib/rest-client";

export class AnaliseConstitucionalidadeService {
  private readonly apiUrl = "/api/analise-constitucionalidade";

  async analisarConstitucionalidade(
    data: AnaliseConstitucionalidadeRequest,
    mandatoId: string
  ): Promise<AnaliseConstitucionalidadeResponse> {
      const formData = this.buildFormData(data);

      const response = await restClient(`${this.apiUrl}/${mandatoId}`, {
        method: "POST",
        body: formData,
      });

      return response.json();
  }

  private buildFormData(data: AnaliseConstitucionalidadeRequest): FormData {
    const formData = new FormData();
    formData.append("file", data.file);

    return formData;
  }
}

// Instância singleton do serviço
export const analiseConstitucionalidadeService =
  new AnaliseConstitucionalidadeService();
