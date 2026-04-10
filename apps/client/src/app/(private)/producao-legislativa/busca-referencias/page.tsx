import { AppHeader } from "@/components/app-header/app-header";
import { BuscaReferencias } from "@/features/busca-referencias/busca-referencias";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Busca de Referências",
};

export default function AnalisarPlExistentePage() {
  return (
    <div>
      <AppHeader
        title="Produção Legislativa"
        breadcrumb={[
          { label: "Produção Legislativa", link: "/producao-legislativa" },
          {
            label: "Busca de Referências",
            link: "/producao-legislativa/busca-referencias",
          },
        ]}
      />

      <BuscaReferencias />
    </div>
  );
}
