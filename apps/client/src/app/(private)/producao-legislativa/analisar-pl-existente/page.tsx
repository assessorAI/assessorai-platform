import { AppHeader } from "@/components/app-header/app-header";

import { AnaliseConstitucionalidade } from "@/features/analise-constitucionalidade/analise-constitucionalidade";

import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Analisar constitucionalidade",
};

export default function AnalisarPlExistentePage() {
  return (
    <div>
      <AppHeader
        title="Produção legislativa"
        breadcrumb={[
          { label: "Produção Legislativa", link: "/producao-legislativa" },
          {
            label: "Analisar constitucionalidade",
            link: "/producao-legislativa/analisar-pl-existente",
          },
        ]}
        description="Analise proposições com auxílio da inteligência artificial"
      />

      <AnaliseConstitucionalidade />
    </div>
  );
}
