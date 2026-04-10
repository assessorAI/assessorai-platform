import { AppHeader } from "@/components/app-header/app-header";
import { CriarPl } from "@/features/criar-pl/criar-pl";

import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Criar Projeto de Lei",
};

export default function CriarPlPage() {
  return (
    <div>
      <AppHeader
        title="Produção Legislativa"
        breadcrumb={[
          { label: "Produção Legislativa", link: "/producao-legislativa" },
          {
            label: "Criar Projeto de Lei",
            link: "/producao-legislativa/criar-pl",
          },
        ]}
        description="Crie um projeto de lei com auxílio da inteligência artificial"
      />

      <CriarPl />
    </div>
  );
}
