import { ENDPOINTS } from "@/config/endpoints";
import { NextRequest, NextResponse } from "next/server";
import { AppThrowError } from "../error/app-throw-error";
import { handleApiError } from "../error/error.handler";
import { apiClient } from "../api-client";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const body = await req.json();
    return body;
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export async function sendPasswordResetHandler(req: NextRequest) {
  const body = await prepareBodyRequest(req);

  try {
    const response = await apiClient.post(
      ENDPOINTS.ADM.SEND_PASSWORD_RESET, 
      body
    );

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}