import { ENDPOINTS } from "@/config/endpoints";
import { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { handleApiError } from "../../error/error.handler";
import {
  AppThrowError,
  AppThrowErrorSpecific,
} from "@/api/error/app-throw-error";
import { friendlyErrorMessage } from "@/api/error/error-map";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const request = await req.json();
    return request;
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export async function checkMandato(req: NextRequest) {
  try {
    const body = await prepareBodyRequest(req);

    const response = await fetch(`${ENDPOINTS.AUTH.CHECK_MANDATO}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, "external");
    }

    const mandatoAlreadyExists = (await response.json()) as { exists: boolean };
    
    if (mandatoAlreadyExists.exists) {
      throw new AppThrowErrorSpecific(
        friendlyErrorMessage.MANDATO_ALREADY_EXISTS
      );
    }

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}