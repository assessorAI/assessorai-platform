import { restClient } from "@/lib/rest-client";

export const forgotPasswordService = {
  forgotPassword: async (email: string) => {
    const response = await restClient(`/api/forgot-password`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    });

    return response.json();
  },
};