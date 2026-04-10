import { NextRequest, NextResponse } from "next/server";
import { handleApiError } from "../error/error.handler";
import { ENDPOINTS } from "@/config/endpoints";
import { AppThrowError } from "../error/app-throw-error";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const body = await req.json();
    return { email: body.email };
  } catch {
    throw new AppThrowError(
      500,
      "internal",
      "Erro ao preparar o corpo da requisição"
    );
  }
};

export async function forgotPasswordHandler(req: NextRequest) {
  try {
    const body = await prepareBodyRequest(req);

    const response = await fetch(`${ENDPOINTS.AUTH.FORGOT_PASSWORD}`, {
      method: "POST",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw AppThrowError.fromFetchResponse(response, "external");
    }

    return NextResponse.json(
      { message: "Email de recuperação enviado com sucesso" },
      { status: 200 }
    );
  } catch (error) {
    return handleApiError(error);
  }
}
