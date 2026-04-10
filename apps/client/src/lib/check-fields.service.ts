import { CheckEmailResponse } from "@/api/register/check-email/check-email.types";
import {
  CheckMandatoRequest,
  CheckMandatoResponse,
} from "@/api/register/check-mandato/check-mandato.types";
import { restClient } from "@/lib/rest-client";

export const checkFieldsService = {
  checkEmail: async (email: string) => {
    const response = await restClient(`/api/check-email?email=${email}`);

    const data = (await response.json()) as unknown as CheckEmailResponse;

    return data;
  },
  checkMandato: async (request: CheckMandatoRequest) => {
    const response = await restClient(`/api/check-mandato`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    const data = (await response.json()) as unknown as CheckMandatoResponse;

    return data;
  }
};
