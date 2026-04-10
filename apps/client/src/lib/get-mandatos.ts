import { restClient } from "./rest-client";

export const getMandatos = async ({ search, offset, limit }: { 
    search: string; 
    offset: number; 
    limit: number; 
  }) => {
    try {
      const params = new URLSearchParams({
        offset: String(offset),
        limit: String(limit),
        orderBy: "nome_parlamentar",
        ...(search && { search }),
      });

      const response = await restClient(`/api/mandatos?${params}`);

      const data = await response.json();

      return {
        data: data.mandatos,
        total: data.total,
        offset: data.offset,
        limit: data.limit,            
        hasMore: (offset + limit) < data.total,
      };
    } catch {
      return {
        data: [],
        total: 0,
        offset: 0,
        limit: limit,
        hasMore: false,
      };
    }
  };
