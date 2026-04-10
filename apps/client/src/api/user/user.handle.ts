import { ENDPOINTS } from "@/config/endpoints";
import { apiClient } from "../api-client";
import { NextRequest, NextResponse } from "next/server";
import { handleApiError } from "../error/error.handler";
import { AppThrowError } from "../error/app-throw-error";
import { UserResponse, UsersParams, UsersResponse } from "./user.types";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const body = await req.json();
    return body;
  } catch  {
    throw new AppThrowError(
      500,
      "internal",
      "Erro ao preparar o corpo da requisição"
    );
  }
};

export const updateUserHandler = async (
  req: NextRequest,
  { id }: { id: string }
) => {
  try {
    const body = await prepareBodyRequest(req);

    const result: UserResponse = await apiClient.put(
      ENDPOINTS.USER.PUT.replace("{id}", id),
      body
    );

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const createUserHandler = async (req: NextRequest) => {
  try {
    const body = await prepareBodyRequest(req);
    const result: UserResponse = await apiClient.post(ENDPOINTS.USER.POST, body);

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const getUsersHandler = async (req: NextRequest) => {
  try {
    const searchParams = req.nextUrl.searchParams;
    const limit = Number(searchParams.get("limit")) || 10;
    const offset = Number(searchParams.get("offset")) || 0;
    const search = searchParams.get("search") || "";
    const role = searchParams.get("role") || "";
    const permission_level = searchParams.get("permission_level") || "";
    const orderBy = searchParams.get("orderBy") || "";
    const from = searchParams.get("from") || "";
    const to = searchParams.get("to") || "";

    const params: UsersParams = { limit, offset, search, role, permission_level, orderBy };

    if (from && to) {
      params.from = from;
      params.to = to;
    }

    const result: UsersResponse = await apiClient.get(
      ENDPOINTS.USER.GET_ALL,
      { params }
    );
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const deleteUserHandler = async ({ id }: { id: string }) => {

  try {
    const result = await apiClient.delete(ENDPOINTS.USER.DELETE.replace("{id}", id));
    
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};