import { ENDPOINTS } from "@/config/endpoints";
import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "../api-client";
import { handleApiError } from "../error/error.handler";
import { verifySession } from "../auth";
import { AppThrowError } from "../error/app-throw-error";
import { MandatosParams, MandatosResponse } from "./mandato.types";

export const updateMandatoHandler = async (req: NextRequest, { id }: { id: string }) => {
  try {
    const body = await req.json();

    const response = await apiClient.put(
      ENDPOINTS.MANDATO.UPDATE.replace("{id}", id),
      body
    );

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const getMandatosHandler = async (req: NextRequest) => {
  try {
    const searchParams = req.nextUrl.searchParams;
    const limit = Number(searchParams.get("limit")) || 10;
    const offset = Number(searchParams.get("offset")) || 0;
    const orderBy = searchParams.get("orderBy") || "";
    const search = searchParams.get("search") || "";
    const cargo_parlamentar = searchParams.get("cargo_parlamentar") || "";
    const casa_legislativa = searchParams.get("casa_legislativa") || "";
    const partido = searchParams.get("partido") || "";
    const perfil_parlamentar = searchParams.get("perfil_parlamentar") || "";
    const espectro_politico = searchParams.get("espectro_politico") || "";
    const from = searchParams.get("from") || "";
    const to = searchParams.get("to") || "";

    const params: MandatosParams = { limit, offset, orderBy, search, cargo_parlamentar, casa_legislativa, partido, perfil_parlamentar, espectro_politico };

    if (from && to) {
      params.from = from;
      params.to = to;
    }

    const response = await apiClient.get(ENDPOINTS.MANDATO.GET_ALL, {
      params
    });

    return NextResponse.json(response as MandatosResponse, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const addUserToMandatoHandler = async (req: NextRequest, { id }: { id: string }) => {
  try {
    const body = await req.json();

    const response = await apiClient.post(
      ENDPOINTS.MANDATO.ADD_USER.replace("{id}", id),
      body
    );

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const deleteUserFromMandatoHandler = async (req: NextRequest, { id, userId }: { id: string, userId: string }) => {
  try {
    const response = await apiClient.delete(
      ENDPOINTS.MANDATO.DELETE_USER.replace("{id}", id).replace("{userId}", userId)
    );
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const addDocumentToMandatoHandler = async (req: NextRequest) => {
  try {
    const params = req.nextUrl.searchParams;
    const mandatoId = params.get("mandato_id");
    const title = params.get("title");
    const fileType = params.get("file_type");

    const body = await req.formData();

    const response = await apiClient.post(
      ENDPOINTS.MANDATO.ADD_DOCUMENT,
      body,
      { params: 
        { mandato_id: mandatoId!, 
          title: title!, 
          file_type: fileType!
        } 
        }
    );
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};

export const deleteDocumentFromMandatoHandler = async (req: NextRequest) => {
  try {
    const params = req.nextUrl.searchParams;
    const fileId = params.get("file_id");
    const response = await apiClient.delete(
      ENDPOINTS.MANDATO.DELETE_DOCUMENT.replace("{file_id}", fileId!)
    );
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Handler para baixar um arquivo do servidor upstream
 * Não utiliza o apiClient, porque ele precisa adicionar cabeçalhos específicos para o
 * repassar o arquivo para o componente.
 */
export const downloadDocumentHandler = async (_req: NextRequest, { id }: { id: string }) => {
  try {
    const session = await verifySession();
    if (!session) {
      return NextResponse.json({ message: "Não autenticado" }, { status: 401 });
    }

    const url = ENDPOINTS.MANDATO.DOWNLOAD_DOCUMENT.replace("{file_id}", id);

    const response = await fetch(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
      },
    });

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, 'external');
    }

    return new Response(response.body, {
      status: 200,
      headers: {
        "Content-Type": response.headers.get("content-type") || "application/octet-stream",
        "Content-Disposition": response.headers.get("content-disposition") || `attachment; filename="${id}"`,
      },
    });
  } catch (error) {
    return handleApiError(error);
  }
};

export const deleteMandatoHandler = async ({ id }: { id: string }) => {
  try {
    const response = await apiClient.delete(ENDPOINTS.MANDATO.DELETE.replace("{id}", id));
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
};