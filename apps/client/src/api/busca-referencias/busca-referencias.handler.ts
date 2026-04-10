import { NextRequest, NextResponse } from "next/server";
import { handleApiError } from "../error/error.handler";
import { apiClient } from "../api-client";
import { ENDPOINTS } from "@/config/endpoints";
import { BuscaReferenciasResponse } from "./busca-referencias.types";
import { AppThrowError } from "../error/app-throw-error";

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const tema = req.nextUrl.searchParams.get("tema")!;
    const offset = req.nextUrl.searchParams.get("offset") || 0;
    const limit = 60;
    return { tema, offset, limit };

  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export const buscaReferenciasHandler = async (req: NextRequest) => {
  try {
    const body = await prepareBodyRequest(req);

    const result: BuscaReferenciasResponse = await apiClient.get(ENDPOINTS.BUSCA_REFERENCIAS.GET, {
      params: {
        query: body.tema,
        limit: body.limit,
        offset: body.offset
      },
    });


    return NextResponse.json(normalizeResults(result), { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

function normalizeResults(response: BuscaReferenciasResponse) {
  return response.projects.map((item) => ({
    id: item.id.toString(),
    title: item.title,
    author: item.author.join(", "),
    footer: item.house,
    subject: item.subject,
    house: item.house,
    chunk_text: item.chunk_text,
    url: item.url,
  }));
}