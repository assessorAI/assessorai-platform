import { ENDPOINTS } from "@/config/endpoints";
import { NextRequest, NextResponse } from "next/server";
import { handleApiError } from "../error/error.handler";
import { AppThrowError } from "../error/app-throw-error";

export async function registerMemberHandler(request: NextRequest) {

    try {
    const body = await request.json();
    const response = await fetch(ENDPOINTS.AUTH.ACTIVATE_ACCOUNT, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {
            "Content-Type": "application/json",
        },
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