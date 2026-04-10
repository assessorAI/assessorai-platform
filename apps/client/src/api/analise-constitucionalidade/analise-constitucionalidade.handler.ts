import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '../error/error.handler';
import { AnaliseConstitucionalidadeResponse } from './analise-constitucionalidade.types';
import { AppThrowError } from '../error/app-throw-error';
import { ENDPOINTS } from '@/config/endpoints';
import { apiClient } from '../api-client';

const prepareBodyRequest = async (req: NextRequest) => {
  try {
  const data = await req.formData();
  
  const file = data.get("file") as File;
  
  const formData = new FormData();
  formData.append("file", file);
  return formData;
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export const analiseConstitucionalidadeHandler = async (req: NextRequest, mandatoId: string) => {
  try {
    const body = await prepareBodyRequest(req);

    const result: AnaliseConstitucionalidadeResponse = await apiClient.post(
      `${ENDPOINTS.ANALISE_CONSTITUCIONALIDADE.CREATE}?mandato_id=${mandatoId}`,
      body
    );


    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

