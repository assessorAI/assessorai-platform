import { ENDPOINTS } from "@/config/endpoints";
import { Mandato } from "../mandato/mandato.types";
import { PermissionLevel } from "@/types/user.types";

export const REGISTER_PATH = ENDPOINTS.AUTH.REGISTER;

export type RegisterResponse = {
  email: string
  first_name: string
  last_name: string
  phone: string
  lgpd_check: boolean
  permission_level: PermissionLevel
  role: string
  mandato: Mandato[]
}

export type RegisterRequest = {
  email: string
  password: string
  first_name: string
  last_name: string
  phone: string
  lgpd_check: string
  permission_level: PermissionLevel
  role: string
  mandato: (MandatoRequest | MandatoIdRequest)[]
}

export type MandatoRequest = {
  nome_parlamentar: string
  casa_legislativa: string
  municipio: string
  ue: string
  perfil_parlamentar: string
  partido: string
  espectro_politico: string
  cargo_parlamentar: string
}

export type MandatoIdRequest = { id: number }
