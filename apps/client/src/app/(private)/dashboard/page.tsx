import { auth } from "@/api/auth/index";

import { AppHeader } from "@/components/app-header/app-header";
import { CardGrid } from "@/components/card-grid";
import { Metadata } from "next";
import { BoltIcon, RectangleStackIcon } from "@heroicons/react/24/outline";
import { BoltIcon as BoltIconSolid, RectangleStackIcon as RectangleStackIconSolid } from "@heroicons/react/24/solid";
import { BrandColor } from "@/types/brand-color.types";

const dashBoardCards = [
  {
    title: "Produção legislativa",
    description:
      "Crie ou analise projetos de lei com auxílio da inteligência artificial",
    icon: (
     <BoltIcon />
    ),
    iconSolid: (
      <BoltIconSolid />
    ),
    link: "/producao-legislativa",
    color: BrandColor.ACCENT,
  },
  {
    title: "Requerimento",
    description:
      "Gere requerimentos formais com estrutura e linguagem adequada",
    icon: <RectangleStackIcon />,
    iconSolid: <RectangleStackIconSolid />,
    link: "/requerimento",
    color: BrandColor.SECONDARY,
  },
];

export const metadata: Metadata = {
  title: "Dashboard - Assesorai",
};

export default async function DashboardPage() {
  const session = await auth();
  const user = session?.user?.first_name;
  const title = user ? `Olá, ${user}` : "Dashboard";

  return (
    <div>
      <AppHeader title={title} />

      <CardGrid title="O que deseja produzir hoje?" cards={dashBoardCards} />
    </div>
  );
}
