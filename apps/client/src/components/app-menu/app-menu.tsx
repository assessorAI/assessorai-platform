"use client";

import { usePathname } from "next/navigation";
import Image from "next/image";
import { Link } from "react-transition-progress/next";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { AppMenuSubmenu } from "./app-menu-submenu";
import { MenuItem } from "./app-menu.types";
import { useSidebar } from "@/components/ui/sidebar";

export function AppMenu({ items, footer, collapsible  }: { items: MenuItem[], footer?: React.ReactNode, collapsible?: "icon" | "offcanvas" }) {
  const pathname = usePathname();
  const { state } = useSidebar();

  return (
    <Sidebar className="bg-[hsl(var(--brand-background))] border-r-0" collapsible={collapsible}>
      <SidebarHeader className="pt-spacing-md px-spacing-sm">
        {state === "expanded" ? (
        <Image src="/logo.svg" alt="Logo" width={163} height={18} />
        ) : (
        <Image src="/short-logo.svg" alt="Logo" width={30} height={30} />
        )}
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup className="border-b border-brand-border px-spacing-sm">
          <SidebarGroupContent>
            <SidebarMenu className="flex flex-col pb-spacing-md">
              {items.map((item: MenuItem) => {
                const isActive = pathname === item.url;
                const hasChildren = !!item.items?.length;

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link
                        href={item.url || ""}
                        className={`${isActive ? "text-brand-primary font-semibold" : "text-gray-500"} flex items-center gap-2 px-spacing-sm py-spacing-md rounded-md w-fit`}
                      >
                        <item.icon className={`${isActive ? "text-brand-primary" : "text-gray-500"} h-4 w-4 stroke-2`} />

                        <span className="text-base">{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                    
                    {hasChildren && 
                      <AppMenuSubmenu item={item}/>
                    }
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {footer && footer}
    </Sidebar>
  );
}
