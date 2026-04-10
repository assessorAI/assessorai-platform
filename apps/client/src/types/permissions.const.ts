import { PermissionLevel } from "./user.types";

export const Permissions: Record<PermissionLevel, string[]> = {
  [PermissionLevel.Admin]: ["*"],

  [PermissionLevel.Manager]: [
    "mandato:perfil_parlamentar:edit",
    "mandato:espectro_politico:edit",
    "mandato:view",
    "mandato:edit",
    "member:add",
    "member:remove",
    "member:view",
    "account:view",
    "mandato:documents:edit",
    "mandato:documents:delete",
  ],

  [PermissionLevel.User]: ["account:view", "mandato:view"],

  [PermissionLevel.Viewer]: ["account:view", "mandato:view"],

  [PermissionLevel.Invited]: [""],
} as const;
