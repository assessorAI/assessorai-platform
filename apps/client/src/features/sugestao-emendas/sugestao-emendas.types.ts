import { Emenda } from "@/api/emenda/emenda.types";


export interface SugestoesEmendasProps {
  sugestoesEmendas: Emenda[];
  onEmendaSelecionada: (emenda: Emenda) => void;
  loading: boolean;
  onClickGerarEmenda: () => void;
}