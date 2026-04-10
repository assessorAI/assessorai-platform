import { AnaliseConstitucionalidadeResponse } from "@/api/analise-constitucionalidade/analise-constitucionalidade.types";

export interface AnaliseConstitucionalidadeProps {
  resultadoAnalise: AnaliseConstitucionalidadeResponse
}

export enum AnaliseConstitucionalidadeParecer {
  FAVORAVEL = "Favorável",
  CONTRARIO = "Contrário",
  FAVORAVEL_COM_RESSALVAS = "Favorável com ressalvas"
}