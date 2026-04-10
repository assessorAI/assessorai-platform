import { AppHeader } from "@/components/app-header/app-header";
import { CardGrid } from "@/components/card-grid";
import { 
  DocumentPlusIcon, 
  CheckBadgeIcon, 
  MagnifyingGlassCircleIcon, 
  SparklesIcon 
} from "@heroicons/react/24/outline";
import { 
  DocumentPlusIcon as DocumentPlusIconSolid,
  CheckBadgeIcon as CheckBadgeIconSolid, 
  MagnifyingGlassCircleIcon as MagnifyingGlassCircleIconSolid, 
  SparklesIcon as SparklesIconSolid 
} from "@heroicons/react/24/solid";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Produção Legislativa - Assesorai"
}

const dashBoardCards = [
  {
    title: "Buscar referências",
    description: "Busque por proposições e anexe as referências no seu novo projeto.",
    icon: <MagnifyingGlassCircleIcon />,
    iconSolid: <MagnifyingGlassCircleIconSolid />,
    link: "/producao-legislativa/busca-referencias",
    bgColor: "bg-brand-accent-40"
  },
  {
    title: "Quero criar Projeto de Lei",
    description: "Crie projetos de lei com auxílio da inteligência artificial",
    icon: <SparklesIcon />,
    iconSolid: <SparklesIconSolid />,
    link: "/producao-legislativa/criar-pl",
    bgColor: "bg-brand-accent-40"
  },
  {
    title: "Analisar Constitucionalidade",
    description: "Analise a constitucionalidade de uma proposição com auxílio da inteligência artificial",
    icon: <CheckBadgeIcon />,
    iconSolid: <CheckBadgeIconSolid />,
    link: "/producao-legislativa/analisar-pl-existente",
    bgColor: "bg-brand-accent-40"
  },
  {
    title: "Sugerir emendas",
    description: "Faça upload de um Projeto de Lei e veja sugestões de emendas feitas pela nossa inteligência artificial.",
    icon: <DocumentPlusIcon />,
    iconSolid: <DocumentPlusIconSolid />,
    link: "/producao-legislativa/sugestao-emendas",
    bgColor: "bg-brand-accent-40"
  }
]

const appHeader = {
  title: "Produção Legislativa",
  description: "Crie ou analise projetos de lei com auxílio da inteligência artificial"
}

const cardGrid = {
  title: "E como você deseja iniciar sua produção legislativa?",
  cards: dashBoardCards
}

export default function ProducaoLegislativaPage() {
  return (
    <div>
      <AppHeader {...appHeader} />
      <CardGrid {...cardGrid} />
    </div>
  )
}