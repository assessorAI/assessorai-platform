export type CheckMandatoResponse = {
    exists: boolean
}

export type CheckMandatoRequest = {
    nome: string
    casa_legislativa: string
    partido: string
    cidade: string
    uf: string
}