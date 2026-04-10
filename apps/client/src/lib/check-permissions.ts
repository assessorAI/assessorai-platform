import { PermissionLevel } from "@/types/user.types";
import { Permissions } from "@/types/permissions.const";

/**
 * Verifica se o usuário tem permissão para executar uma ação
 * @param role - O nível de permissão do usuário
 * @param action - A ação que o usuário deseja executar
 * @returns true se o usuário tem permissão, false caso contrário
 */
export function hasPermission(role: PermissionLevel, action: string) {
    const rolePermissions = Permissions[role] ?? [];
    return rolePermissions.includes("*") || rolePermissions.includes(action);
}