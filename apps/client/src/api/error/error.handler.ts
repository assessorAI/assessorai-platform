import { NextResponse } from "next/server";
import { AppThrowError, AppThrowErrorSpecific } from "./app-throw-error";
import { errorMap } from "./error-map";

/**
 * handleApiError
 * 
 * Função central para tratar de forma unificada os erros provenientes das APIs.
 * 
 * Parâmetros:
 *   - error: unknown
 *     O erro capturado, pode ser instância de AppThrowError, TypeError, Error genérico ou qualquer valor.
 * 
 * Retorna:
 *   - NextResponse
 *     Resposta HTTP com mensagem de erro apropriada e status code correspondente, 
 *     seguindo o tipo/detalhe do erro recebido.
 * 
 * Exemplos de uso:
 *   return handleApiError(error);
 */
export const handleApiError = (error: unknown) => {

  if (error instanceof AppThrowErrorSpecific) {
    return NextResponse.json(
      { error: error.message },
      { status: 400 } 
    );
  }
  if (error instanceof AppThrowError) {
    return NextResponse.json(
      { error: error.customMessage || errorMap[500] },
      { status: error.status }
    );
  }

  // Se é erro de rede (servidor sem conexão ao backend)
  if (error instanceof TypeError) {
    return NextResponse.json({ error: errorMap[503] }, { status: 503 });
  }

  // Se é Error genérico
  if (error instanceof Error) {
    console.error('Erro não tratado no handler:', {
      name: error.name,
      message: error.message,
      stack: error.stack,
    });

    return NextResponse.json(
      { error: errorMap[500] },
      { status: 500 }
    );
  }

  return NextResponse.json(
    { error: errorMap[500] },
    { status: 500 }
  );
};
