import { AppHeader } from "@/components/app-header/app-header";
import { SugestaoEmendas } from "@/features/sugestao-emendas/sugestao-emendas";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sugestão de emendas",
};

export default function SugestaoEmendasPage() {
  return (
    <div>
      <AppHeader
        title="Produção legislativa"
        breadcrumb={[
          { label: "Produção Legislativa", link: "/producao-legislativa" },
          {
            label: "Sugestão de emendas",
            link: "/producao-legislativa/sugestao-emendas",
          },
        ]}
        description="Faça upload de um Projeto de Lei e veja sugestões de emendas feitas pela nossa inteligência artificial."
      />

      <SugestaoEmendas />
    </div>
  );
}
