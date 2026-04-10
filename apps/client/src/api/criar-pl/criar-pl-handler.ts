import { NextRequest, NextResponse } from "next/server";
import { handleApiError } from "../error/error.handler";
import { apiClient } from "../api-client";
import { ENDPOINTS } from "@/config/endpoints";
import { CriarPLResponse } from "./criar-pl.types";
import { AppThrowError } from "../error/app-throw-error";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    return await req.text();
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export const criarPLHandler = async (req: NextRequest, mandatoId: string) => {
  try {
    const body = await prepareBodyRequest(req);

    const result: CriarPLResponse = await apiClient.post(`
      ${ENDPOINTS.CRIAR_PL.CREATE}?mandato_id=${mandatoId}`, 
      body
    );

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};
