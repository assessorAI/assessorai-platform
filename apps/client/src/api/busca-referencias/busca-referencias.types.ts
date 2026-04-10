export type BuscaReferenciasResponse = {
  projects: {
    id: number;
    title: string;
    house: string;
    author: string[];
    subject: string;
    chunk_text: string;
    year: number;
    score: number;
    url: string;
    metadata: {
      creation_time: string | null;
      last_update_time: string | null;
      distance: string | null;
      certainty: string | null;
      score: number;
      explain_score: string;
      is_consistent: string | null;
      rerank_score: string | null;
    };
  }[];
};

export type BuscaReferenciasRequest = {
  query: string;
  limit?: number;
};