import { AppThrowError } from "@/api/error/app-throw-error";
import { errorMap } from "@/api/error/error-map";

export const restClient = async (
  url: string,
  options?: RequestInit
): Promise<Response> => {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      let customMessage: string | undefined;
      
      try {
        const errorData = await response.json();
        customMessage = errorData.error || errorData.details; 
      } catch {
        // Se falhar ao ler JSON, deixa undefined
      }

      // Se não houver mensagem específica, usa errorMap
      if (!customMessage && response.status in errorMap) {
        customMessage = errorMap[response.status as keyof typeof errorMap];
      }

      throw new AppThrowError(response.status, "external", customMessage);
    }

    return response;
  } catch (error) {

    // AbortError serve para cancelar a requisição se o componente for desmontado
    if (error instanceof Error && error.name === 'AbortError') {
      throw error;
    }

    if (error instanceof TypeError) {
      throw new AppThrowError(503, "internal", errorMap[503]);
    }

    if (error instanceof AppThrowError) throw error;

    throw new AppThrowError(500, "internal", errorMap[500]);
  }
};