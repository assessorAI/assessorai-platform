export interface AnaliseConstitucionalidadeRequest {
  file: File;
}

export interface AnaliseConstitucionalidadeResponse {
  parecer: string
  gravidade: string
  justificativa: string
  artigos_destacados: string[]
  sugestao: string
}