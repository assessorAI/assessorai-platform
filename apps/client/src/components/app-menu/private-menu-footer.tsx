import {
  ChevronDownIcon,
  ChevronUpIcon,
  Cog6ToothIcon,
  UserIcon,
  ArrowLeftStartOnRectangleIcon,
  ChatBubbleOvalLeftEllipsisIcon,
  BuildingLibraryIcon,
  KeyIcon,
} from "@heroicons/react/24/outline";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import {
  SidebarFooter,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "../ui/sidebar";
import { Skeleton } from "../ui/skeleton";
import { signOut, useSession } from "next-auth/react";
import { AvatarLetter } from "../avatar-letter";
import { useState } from "react";
import Link from "next/link";
import { PermissionLevel } from "@/types/user.types";
import { hasPermission } from "@/lib/check-permissions";
import { usePathname } from "next/navigation";

export function PrivateMenuFooter() {
  const { data: session, status } = useSession();
  const [isOpen, setIsOpen] = useState(false);
  const isLoading = status === "loading";
  const permissionLevel = session?.user?.permission_level;
  const pathname = usePathname();

  const nameAvatar = session?.user ? `${session?.user?.first_name?.slice(0, 1)}${session?.user?.last_name?.slice(0, 1)}` : "";

  const canViewAction = (action: string) => {
    return hasPermission(permissionLevel as PermissionLevel, action);
  };

  const handleSignOut = () => {
    signOut({ callbackUrl: "/login" });
  };

  if (!isLoading && session?.user?.mandato.length === 0) {
    handleSignOut();
  }

  const menuItemsFooter = [
    {
      title: "Precisando de apoio?",
      url: `${process.env.NEXT_PUBLIC_LINK_PRECISANDO_AJUDA}`,
      icon: ChatBubbleOvalLeftEllipsisIcon,
      newTab: true
    },
  ];

  const menuItemsDropdownFooter = [
    {
      title: "Configurações do Adm",
      url: `/adm/dashboard`,
      icon: KeyIcon,
      visible: canViewAction("*"),
      newTab: true
    },
    {
      title: canViewAction("mandato:edit") ? "Configurar mandato" : "Dados do mandato",
      url: `/mandato/${session?.user?.mandato[0].id}/configurar`,
      icon: canViewAction("mandato:edit") ? Cog6ToothIcon : BuildingLibraryIcon,
      visible: canViewAction("mandato:view"),
      newTab: false
    },
    {
      title: "Dados da conta",
      url: `/dados-conta`,
      icon: UserIcon,
      visible: canViewAction("account:view"),
      newTab: false
    },
  ];

  return (
    <SidebarFooter>
      <SidebarMenu>
        {menuItemsFooter.map((item) => {
          const isActive = pathname === item.url;
          return (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild isActive={isActive}>
                <Link
                  href={item.url || ""}
                  target={item.newTab ? "_blank" : "_self"}
                  rel={item.newTab ? "noopener noreferrer" : undefined}
                  className={`${
                    isActive
                      ? "text-brand-primary font-semibold"
                      : "text-gray-500"
                  } flex items-center gap-2 px-spacing-sm py-spacing-md rounded-md w-full`}
                >
                  <item.icon
                    className={`${
                      isActive ? "text-brand-primary" : "text-gray-500"
                    } h-4 w-4 stroke-2`}
                  />

                  <span className="text-base">{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
        <SidebarMenuItem className="h-[64px]">
          <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton className="h-full bg-white rounded-md border border-gray-200">
                {isLoading ? (
                  <Skeleton className="h-4 w-24" aria-hidden />
                ) : (
                  <>
                  {session?.user?.first_name && (
                    <>
                    <AvatarLetter
                      letter={nameAvatar}
                    />
                    <div className="flex flex-col items-start">
                      <span className="text-sm font-semibold">
                        {session?.user?.first_name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {session?.user?.role}
                      </span>
                    </div>
                    </>
                    )}
                  </>
                )}
                {isOpen ? (
                  <ChevronUpIcon className="ml-auto" />
                ) : (
                  <ChevronDownIcon className="ml-auto" />
                )}
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              side="top"
              className="w-[--radix-popper-anchor-width]"
            >
              {menuItemsDropdownFooter.map((item) => {
                if (!item.visible) return null;
                return (
                  <DropdownMenuItem key={item.title}>
                    <Link 
                    href={item.url} 
                    target={item.newTab ? "_blank" : "_self"}
                  rel={item.newTab ? "noopener noreferrer" : undefined}
                    className="w-full">
                      <div className="flex items-center gap-1">
                        <item.icon className="h-4 w-4" />
                        {item.title}
                      </div>
                    </Link>
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <button onClick={() => signOut({ callbackUrl: "/login" })} className="w-full">
                  <div className="flex items-center gap-1">
                    <ArrowLeftStartOnRectangleIcon className="h-4 w-4" />
                    Sair
                  </div>
                </button>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  );
}
