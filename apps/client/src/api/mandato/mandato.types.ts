import { UserResponse } from "../user/user.types"

export type Gerente = {
    id: number
    nome: string
    email: string
}

export type Mandato = {
    nome_parlamentar: string
    casa_legislativa: string
    municipio: string
    ue: string
    cargo_parlamentar: string
    temas_interesse?: string | null
    perfil_parlamentar: string
    espectro_politico: string
    partido: string
    created_at: string
    id: number
    users: number[]
    gerente: Gerente[]
    last_login: { email: string, date: string } | null
    numero_atividades: number
}

export type DocumentosCasaParamsRequest = {
    mandato_id: string
    title: string
    file_type: string
}

export type DocumentosCasaBodyRequest = {
    file: File
}

export type MandatoUsersResponse = {
    users: UserResponse[]
}

export type MandatosResponse = {
    mandatos: Mandato[]
}

export type MandatoWithUsers = Omit<Mandato, 'users'> & {
    users: UserResponse[]
}

export type MandatosParams = {
    limit?: number,
    offset?: number,
    orderBy?: string,
    search?: string,
    cargo_parlamentar?: string,
    casa_legislativa?: string,
    partido?: string,
    perfil_parlamentar?: string,
    espectro_politico?: string,
    from?: string,
    to?: string
}