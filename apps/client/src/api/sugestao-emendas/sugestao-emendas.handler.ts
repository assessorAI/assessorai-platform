import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '../error/error.handler';
import { SugestaoEmendasResponse } from '@/api/sugestao-emendas/sugestao-emendas.types';
import { AppThrowError } from '../error/app-throw-error';
import { apiClient } from '../api-client';
import { ENDPOINTS } from '@/config/endpoints';

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const formData = await req.formData();
    return formData;
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}
export const sugestaoEmendasHandler = async (req: NextRequest, mandatoId: string) => {
  try {
    const body = await prepareBodyRequest(req);

    const result: SugestaoEmendasResponse = await apiClient.post(`
      ${ENDPOINTS.SUGESTAO_EMENDAS.CREATE}?mandato_id=${mandatoId}`, 
      body
    );

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};