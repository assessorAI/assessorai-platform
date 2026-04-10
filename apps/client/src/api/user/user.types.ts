import { PermissionLevel } from "@/types/user.types"
import { Mandato } from "../mandato/mandato.types"

export type UserResponse = {
    email: string
    first_name: string
    last_name: string
    phone: string
    permission_level: PermissionLevel
    lgpd_check: boolean
    role: string
    is_active?: boolean
    id: string
    mandato: Mandato[]
    last_login: string
}

export type UsersResponse = {
    users: UserResponse[],
    total: number,
    limit: number,
    offset: number
}

export type UsersParams = {
    limit?: number,
    offset?: number,
    search?: string,
    role?: string,
    permission_level?: string,
    orderBy?: string,
    from?: string,
    to?: string
}