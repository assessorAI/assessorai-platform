import { ProjetoReferencia } from "@/context/projetos-referencias.context";

export interface BuscaReferenciasResultProps {
  results: ProjetoReferencia[];
  searchedTerm: string;
  onReachEnd: (offset: number) => void;
  isLoading: boolean;
} 

export enum SelectedHouse {
  ALL = "all",
  OTHER = "other",
  MY_HOUSE = "my_house",
}