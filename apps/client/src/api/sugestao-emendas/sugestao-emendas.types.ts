import { Emenda } from "../emenda/emenda.types";

// Tipos específicos para sugestão de emendas
export interface SugestaoEmendasRequest {
  file: File;
  // Dados do parlamentar (temporários - depois virão do token)
  nome_parlamentar?: string;
  casa_legislativa?: string;
  esfera?: string;
  municipio?: string;
  ue?: string;
  temas_interesse?: string;
  perfil_parlamentar?: string;
  espectro_politico?: string;
  data?: string;
  origem_legislativa?: string;
  // Outros campos que podem vir do formulário
  [key: string]: unknown;
}

export interface SugestaoEmendasResponse {
  emendas: Emenda[];
}