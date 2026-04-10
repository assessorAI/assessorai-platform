"use client";

import { HomeIcon, RectangleStackIcon } from "@heroicons/react/24/solid";
import { BoltIcon } from "@heroicons/react/24/solid";
import { MenuItem } from "./app-menu.types";
import { AppMenu } from "./app-menu";
import { PrivateMenuFooter } from "./private-menu-footer";

const items: MenuItem[] = [
    {
      title: "Painel",
      url: "/dashboard",
      icon: HomeIcon,
    },
    {
      title: "Produção Legislativa",
      url: "/producao-legislativa",
      icon: BoltIcon,
      items: [
        {
          title: "Busca de Referências",
          url: "/producao-legislativa/busca-referencias",
        },
        { title: "Criar Projeto de Lei", url: "/producao-legislativa/criar-pl" },
        {
          title: "Constitucionalidade",
          url: "/producao-legislativa/analisar-pl-existente",
        },
        {
          title: "Sugestão de Emendas",
          url: "/producao-legislativa/sugestao-emendas",
        },
      ],
    },
    {
      title: "Requerimentos e indicações",
      url: "/requerimento",
      icon: RectangleStackIcon,
    },
  ];

export function PrivateMenu() {
  return (
    <AppMenu items={items} footer={<PrivateMenuFooter />}/>
  );
}