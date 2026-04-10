export enum POSICIONAMENTO_MANDATO {
  DE_ESQUERDA = "De esquerda",
  DE_CENTRO_ESQUERDA = "De centro esquerda",
  CENTRO = "De centro",
  DE_CENTRO_DIREITA = "De centro direita",
  DE_DIREITA = "De direita",
}

export enum cargoParlamentarEnum {
  VEREADOR = "Vereador",
  DEP_ESTADUAL = "Deputado Estadual",
  DEP_FEDERAL = "Deputado Federal",
  SENADOR = "Senador"
} 

export enum casaLegislativaEnum {
  CAMARA_MUNICIPAL = "Câmara Municipal",
  CAMARA_ESTADUAL = "Câmara Estadual",
  CAMARA_FEDERAL = "Câmara Federal",
  SENADO = "Senado"
}

export const PERFIS_MANDATO = [
  {
    value: "Articulador",
    label: "Articulador",
    desc: "Construir alianças, mediar conflitos e promover o diálogo entre diferentes atores para assegurar avanços legislativos.",
  },
  {
    value: "Fiscalizador",
    label: "Fiscalizador",
    desc: "Monitorar a atuação do Executivo e demais órgãos públicos, garantindo o cumprimento das leis, a transparência e a responsabilidade no uso de recursos públicos.",
  },
  {
    value: "Legislador",
    label: "Legislador",
    desc: "Criação, análise e aprimoramento de lei, desenvolvendo propostas, revisando e ajustando leis existentes para mantê-las adequadas e eficazes.",
  },
] as const;