import { restClient } from "@/lib/rest-client";

export const resetPasswordService = {
  resetPassword: async (token: string, password: string) => {
    const response = await restClient(`/api/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ token, password }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    return response.json();
  },
};