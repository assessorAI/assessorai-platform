import { Municipio, UF } from "@/api/gov/api-gov.types";
import { ENDPOINTS } from "@/config/endpoints";

export const getFieldsService = {
  buscarUFs: async () => {
    const response = await fetch(ENDPOINTS.BUSCA_UF.GET);

    const ufOrdered = (await response.json()).sort((a: UF, b: UF) => a.nome.localeCompare(b.nome));

    if (!response.ok) {
      throw new Error("Erro ao buscar UFs");
    }
    return ufOrdered;
  },
  getMunicipios: async (uf: string) => {
    const url = ENDPOINTS.BUSCA_MUNICIPIOS.GET.replace("{UF}", uf);

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error("Erro ao buscar Municípios");
      }

      const data = await response.json();
      return data as unknown as Municipio[];
    } catch (error) {
      throw error;
    }
  },
  getCasaLegislativa: (cargo: string, uf: string, municipio: string | undefined) => {
    const cargoLower = cargo.toLowerCase();
    const ufLower = uf.toLowerCase();
    const preposicao = getPreposicao(uf);

    if (ufLower === "distrito federal" && cargoLower === "deputado estadual") {
      return "Câmara Legislativa do Distrito Federal";
    }

    if (cargoLower === "vereador" && !municipio) {
      return ""
    }

    switch (cargoLower) {
      case "vereador":
        return `Câmara Municipal de ${municipio}`;
      case "deputado estadual":
        return `Assembleia Legislativa do Estado ${preposicao} ${uf}`;
      case "deputado federal":
        return "Câmara dos Deputados";
      case "senador":
        return "Senado Federal";
      default:
        return "Casa legislativa não encontrada";
    }
  },
};

const preposicoesEspeciais: Record<string, string> = {
  Alagoas: "de",
  Bahia: "da",
  Goiás: "de",
  MatoGrosso: "de",
  MatoGrossoDoSul: "de",
  MinasGerais: "de",
  Pernambuco: "de",
  Rondônia: "de",
  Roraima: "de",
  SantaCatarina: "de",
  SãoPaulo: "de",
  Sergipe: "de",
  DistritoFederal: "do",
};

function getPreposicao(uf: string) {
  const key = uf.replace(/\s+/g, "");
  return preposicoesEspeciais[key] || (uf.endsWith("s") ? "de" : "do");
}