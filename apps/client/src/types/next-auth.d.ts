import { DefaultSession } from "next-auth"
import { PermissionLevel } from "./user.types"
import { Mandato } from "@/api/mandato/mandato.types"

declare module "next-auth" {
  interface User {
    id: string
    email: string
    first_name: string
    last_name: string
    role: string
    accessToken: string
    casa_legislativa: string
    permission_level: PermissionLevel
    phone: string
    lgpd_check: boolean
    municipio: string
    ue: string
    mandato: Mandato[]
  }
}

declare module "next-auth" {
  interface Session {
    accessToken: string
    expiresAt: string
    user: {
     User
    } & DefaultSession["user"]
  }
}