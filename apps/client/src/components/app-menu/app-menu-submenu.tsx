
import {
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
} from "@/components/ui/sidebar";
import { MenuItem } from "./app-menu.types";
import { usePathname } from "next/navigation";
import { Link } from "react-transition-progress/next";

export function AppMenuSubmenu({
  item
}: {
  item: MenuItem;
}) {
  const pathname = usePathname();
  
  return (
  <SidebarMenuSub className="py-1 ml-5 gap-spacing-xs">
  {item.items!.map((item) => (
    <SidebarMenuSubItem key={item.title}>
      <SidebarMenuSubButton asChild isActive={pathname === item.url} >
        <Link href={item.url} className={`${pathname === item.url ? "text-brand-primary font-semibold" : "text-gray-500"}`}>{item.title}</Link>
      </SidebarMenuSubButton>
    </SidebarMenuSubItem>
  ))}
</SidebarMenuSub>
  );
}
