import { verifySession } from "./auth";
import { ENDPOINTS } from "@/config/endpoints";
import { AppThrowError } from "./error/app-throw-error";

/**
 * Cliente HTTP configurado para comunicação com backend externo
 * Utiliza o token de autenticação para fazer as requisições
 * Se o endpoint for público, não utiliza o token de autenticação
 * Se o endpoint for privado, utiliza o token de autenticação
 */
export class ApiClient {
  private readonly PUBLIC_ENDPOINTS = ENDPOINTS.AUTH;

  async post<TResponse = unknown>(endpoint: string, data: FormData | Record<string, unknown> | string, options?: { params?: Record<string, string | number | boolean> }): Promise<TResponse> {
    return this.request<TResponse>("POST", endpoint, data, options);
  }

  async put<TResponse = unknown>(endpoint: string, data: FormData | Record<string, unknown> | string): Promise<TResponse> {
    return this.request<TResponse>("PUT", endpoint, data);
  }

  async delete<TResponse = unknown>(endpoint: string): Promise<TResponse> {
    return this.request<TResponse>("DELETE", endpoint);
  }

  private async request<TResponse = unknown>(
    method: "POST" | "PUT" | "DELETE",
    endpoint: string,
    data?: FormData | Record<string, unknown> | string,
    options?: { params?: Record<string, string | number | boolean> }
  ): Promise<TResponse> {
    const config: RequestInit = { method };
    let response: Response;

    const url = this.addParamsUrl(endpoint, options?.params);

    const configWithAuth = await this.addHeaderAuthorization(endpoint, config);
    
    if (data) {
      const configWithHeaders = this.addContentTypeHeader(configWithAuth, data);
      configWithHeaders.body = this.prepareBody(data);
      
      response = await fetch(url.toString(), configWithHeaders);
    } else {
      response = await fetch(url.toString(), configWithAuth);
    }

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, 'external');
    }

    return response.json();
  }

  private addContentTypeHeader(
    config: RequestInit,
    data: FormData | Record<string, unknown> | string
  ): RequestInit {
    const contentType = this.getContentType(data);

    if (contentType) {
      config.headers = {
        "Content-Type": contentType,
        ...config.headers,
      };
    }

    return config;
  }

  private prepareBody(
    data: FormData | Record<string, unknown> | string
  ): BodyInit {
    if (data instanceof FormData || typeof data === "string") {
      return data;
    }
    return JSON.stringify(data);
  }

  async get<TResponse = unknown>(
    endpoint: string,
    options?: { params?: Record<string, string | number | boolean> }
  ): Promise<TResponse> {
    const url = this.addParamsUrl(endpoint, options?.params);

    const config: RequestInit = {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
    };

    const configWithAuthorization = await this.addHeaderAuthorization(
      endpoint,
      config
    );

    const response = await fetch(url.toString(), configWithAuthorization);

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, 'external');
    }

    return response.json();
  }

  private addParamsUrl(
    endpoint: string,
    params?: Record<string, string | number | boolean>
  ): URL {
    const url = new URL(endpoint);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.set(key, String(value));
      });
    }

    return url;
  }

  private async addHeaderAuthorization(
    endpoint: string,
    config: RequestInit
  ): Promise<RequestInit> {
    if (!this.isPublicEndpoint(endpoint)) {
      const authorizationHeader = await this.getAuthorizationHeader();
      config.headers = {
        ...config.headers,
        Authorization: authorizationHeader,
      };
    }

    return config;
  }

  private isPublicEndpoint(path: string): boolean {
    return Object.values(this.PUBLIC_ENDPOINTS).includes(path);
  }

  private async getAuthorizationHeader(): Promise<string> {
    const session = await verifySession();

    if (!session || !session.accessToken) {
      throw new AppThrowError(401, 'internal');
    }
    return `Bearer ${session.accessToken}`;
  }

  private getContentType(
    data: FormData | Record<string, unknown> | string
  ): string | null {
    if (data instanceof FormData) {
      return null;
    }

    if (typeof data === "string") {
      return "application/x-www-form-urlencoded";
    }

    return "application/json";
  }
}

export const apiClient = new ApiClient();
