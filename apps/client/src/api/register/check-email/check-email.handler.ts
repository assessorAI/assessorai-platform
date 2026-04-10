import { ENDPOINTS } from "@/config/endpoints";
import { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { CheckEmailResponse } from "./check-email.types";
import { handleApiError } from "../../error/error.handler";
import { AppThrowError, AppThrowErrorSpecific } from "../../error/app-throw-error";
import { friendlyErrorMessage } from "@/api/error/error-map";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const email = req.nextUrl.searchParams.get("email");
    return { email };
  } catch {
    throw new AppThrowError(
      500,
      "internal",
      "Erro ao preparar o corpo da requisição"
    );
  }
};
export async function checkEmail(req: NextRequest) {
  try {
    const body = await prepareBodyRequest(req);

    const response = await fetch(
      `${ENDPOINTS.AUTH.CHECK_EMAIL}?email=${body.email}`
    );

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, "external");
    }

    const data = (await response.json()) as unknown as CheckEmailResponse;

    if (data.exists) {
      throw new AppThrowErrorSpecific(friendlyErrorMessage.EMAIL_ALREADY_IN_USE);
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}