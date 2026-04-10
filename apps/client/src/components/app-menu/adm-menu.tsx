"use client";

import { ChartPieIcon, UserGroupIcon, BuildingLibraryIcon } from "@heroicons/react/24/solid";
import { MenuItem } from "./app-menu.types";
import { AppMenu } from "./app-menu";

const items: MenuItem[] = [
    {
      title: "Dashboard geral",
      url: "/adm/dashboard",
      icon: ChartPieIcon,
    },
    {
      title: "Gestão de usuários",
      url: "/adm/gestao-usuarios",
      icon: UserGroupIcon,
    },
    {
      title: "Gestão de mandatos",
      url: "/adm/gestao-mandatos",
      icon: BuildingLibraryIcon,
    },
    // {
    //   title: "Gestão de logs",
    //   url: "/adm/gestao-logs",
    //   icon: BookOpenIcon,
    // },
  ];

export function AdmMenu() {
  return (
    <AppMenu items={items} collapsible="icon" />
  );
}