import { ENDPOINTS } from "@/config/endpoints";
import { apiClient } from "../api-client";
import { UserResponse, UsersResponse } from "./user.types";
import { AppThrowError } from "../error/app-throw-error";

export const userService = {
  getUser: async (id: number) => {
    return await apiClient.get<UserResponse>(
      ENDPOINTS.USER.GET.replace("{id}", id.toString())
    );
  },
  getUsers: async (limit: number, offset: number) => {
    return await apiClient.get<UsersResponse>(
      ENDPOINTS.USER.GET_ALL,
      {
        params: {
          limit,
          offset,
        },
      }
    );
  },
  getUserByToken: async (token: string) => {
    const response = await fetch(
      `${ENDPOINTS.AUTH.ACTIVATE_ACCOUNT}?token=${token}`
    );
    if (!response.ok)
      throw await AppThrowError.fromFetchResponse(response, "external");

    return response.json();
  },
};
