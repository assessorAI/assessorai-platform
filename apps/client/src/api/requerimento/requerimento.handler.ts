import { NextRequest, NextResponse } from "next/server";
import { handleApiError } from "../error/error.handler";
import { ENDPOINTS } from "@/config/endpoints";
import { RequerimentoResponse } from "./requerimento.types";
import { apiClient } from "../api-client";
import { AppThrowError } from "../error/app-throw-error";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    return await req.text();
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export const requerimentoHandler = async (req: NextRequest, mandatoId: string) => {
  try {
    const body = await prepareBodyRequest(req);

    const result: RequerimentoResponse = await apiClient.post(`
      ${ENDPOINTS.REQUERIMENTO.CREATE}?mandato_id=${mandatoId}`, 
      body
    );

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};