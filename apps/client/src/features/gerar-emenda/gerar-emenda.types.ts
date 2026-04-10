import { Emenda } from "@/api/emenda/emenda.types";

export interface GerarEmendaProps {
  sugestaoEmenda: Emenda;
  file: File;
  onEmendaGerada: () => void;
}