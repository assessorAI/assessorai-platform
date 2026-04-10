// Tipos específicos para emenda
export interface CreateEmendaRequest {
  file: File;
  art: string;
  tipo: string;
  texto: string;
  // Dados do parlamentar (temporários - depois virão do token)
  nome_parlamentar?: string;
  casa_legislativa?: string;
  esfera?: string;
  municipio?: string;
  ue?: string;
  temas_interesse?: string;
  perfil_parlamentar?: string;
  data?: string;
  espectro_politico?: string;
  origem_legislativa?: string;
}

export interface CreateEmendaResponse {
  art: number;
  tipo: string;
  texto: string;
  justificativa: string;
  full_markdown: string;
}

export interface Emenda {
  art: number;
  tipo: string;
  texto: string;
}