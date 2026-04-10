import { ENDPOINTS } from "@/config/endpoints";
import { handleApiError } from "../error/error.handler";
import { NextRequest, NextResponse } from "next/server";
import { AppThrowError } from "../error/app-throw-error";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const body = await req.json();
    return { token: body.token, password: body.password };
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}
export async function resetPasswordHandler(req: NextRequest) {
  try {
    const body = await prepareBodyRequest(req);
    const token = body.token;
    const new_password = body.password;

    const response = await fetch(`${ENDPOINTS.AUTH.RESET_PASSWORD}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, new_password })
    });

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, "external");
    }

    const data = await response.json() as unknown;

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}