export enum PermissionLevel {
  Admin = "Admin",
  Manager = "Manager",
  User = "User",
  Viewer = "Viewer",
  Invited = "Invited",
}

export const PermissionLevelOptions = [
  { value: PermissionLevel.Admin, label: "Administrador" },
  { value: PermissionLevel.Manager, label: "Gerente do mandato" },
  { value: PermissionLevel.User, label: "Membro do mandato" }
] as const;

export const cargo = [
  "Chefe de Gabinete",
  "Coordenador Legislativo",
  "Coordenador de Comunicação",
  "Assessor Jurídico",
  "Assessor Legislativo",
  "Assessor de Demandas",
  "Assessor de comunicação",
  "Assessor administrativo",
  "Assessor político/Articulação",
] as const;


export enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
}